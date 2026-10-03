"""Projeto 6: triagem explicável de incidentes de rede de um laboratório.

Cláusulas de Horn proposicionais; encadeamento para frente com agenda e
encadeamento para trás orientado a consulta. Não há probabilidades ou negação
por falha. 'Indisponível' precisa ser observado/derivado, nunca vem da ausência.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from .comum import salvar, plotar, FIGURAS


@dataclass(frozen=True)
class Regra:
    nome: str
    premissas: tuple
    conclusao: str


# Base de conhecimento: cada regra é uma cláusula de Horn (premissas -> conclusão).
# R01-R10 e R16 diagnosticam e recomendam; R11-R14 detectam observações
# contraditórias; R15 confirma operação normal.
REGRAS = [
    Regra("R01", ("sem_link", "cabo_danificado"), "falha_fisica"),
    Regra("R02", ("falha_fisica",), "trocar_cabo"),
    Regra("R03", ("link_ativo", "sem_ip", "dhcp_inativo"), "falha_dhcp"),
    Regra("R04", ("falha_dhcp",), "acionar_dhcp"),
    Regra("R05", ("ip_valido", "gateway_responde", "dns_falha"), "falha_dns"),
    Regra("R06", ("falha_dns",), "revisar_dns"),
    Regra("R07", ("ip_valido", "gateway_falha", "outros_afetados"), "falha_gateway"),
    Regra("R08", ("falha_gateway",), "acionar_rede"),
    Regra("R09", ("ip_valido", "gateway_responde", "dns_responde", "servico_falha"), "falha_servico"),
    Regra("R10", ("falha_servico",), "acionar_servico"),
    Regra("R11", ("gateway_responde", "gateway_falha"), "evidencia_inconsistente"),
    Regra("R12", ("dns_responde", "dns_falha"), "evidencia_inconsistente"),
    Regra("R13", ("link_ativo", "sem_link"), "evidencia_inconsistente"),
    Regra("R14", ("evidencia_inconsistente",), "recoletar_evidencias"),
    Regra("R15", ("ip_valido", "gateway_responde", "dns_responde", "servico_responde"), "rede_operacional"),
    Regra("R16", ("falha_fisica", "outros_afetados"), "inspecionar_switch"),
]

CONSULTAS = ["trocar_cabo", "acionar_dhcp", "revisar_dns", "acionar_rede",
             "acionar_servico", "recoletar_evidencias", "rede_operacional", "inspecionar_switch"]


def frente(fatos, regras=REGRAS):
    """Cada premissa conhecida decrementa o contador da regra uma única vez.

    O fecho contém exatamente as consequências positivas alcançáveis. As
    provas registram a primeira regra usada para cada conclusão nova.
    """
    conhecidos = set(fatos)
    provas = {f: {"fato": f} for f in conhecidos}
    agenda = deque(sorted(conhecidos))
    # indice: premissa -> regras que a usam; restantes: premissas ainda não provadas.
    indice = defaultdict(list)
    restantes = []
    for i, r in enumerate(regras):
        premissas = set(r.premissas)
        restantes.append(len(premissas))
        for p in premissas:
            indice[p].append(i)
    disparadas, processados = 0, 0
    def concluir(r):
        nonlocal disparadas
        disparadas += 1
        if r.conclusao not in conhecidos:
            conhecidos.add(r.conclusao)
            provas[r.conclusao] = {"regra": r.nome, "conclusao": r.conclusao,
                                  "premissas": [provas[p] for p in r.premissas]}
            agenda.append(r.conclusao)
    # Regras sem premissas valem incondicionalmente.
    for i, r in enumerate(regras):
        if restantes[i] == 0:
            concluir(r)
    # Cada símbolo sai da agenda uma vez, logo o custo é linear no tamanho da base.
    while agenda:
        p = agenda.popleft(); processados += 1
        for i in indice[p]:
            restantes[i] -= 1
            if restantes[i] == 0:
                concluir(regras[i])
    return conhecidos, provas, {"regras_disparadas": disparadas, "fatos_processados": processados}


def tras(consulta, fatos, regras=REGRAS):
    """OR entre regras para a consulta; AND entre premissas de cada regra.

    Bloqueio por ancestrais impede ciclos sem inventar provas. Cache conserva
    só sucessos: falhas em presença de ciclos podem depender dos ancestrais.
    """
    indice = defaultdict(list)
    for regra in regras:
        indice[regra.conclusao].append(regra)
    cache, met = {}, {"chamadas": 0, "regras_tentadas": 0}
    def provar(alvo, ancestrais):
        met["chamadas"] += 1
        if alvo in fatos:
            return {"fato": alvo}
        if alvo in cache:
            return cache[alvo]
        if alvo in ancestrais:
            return None  # O alvo depende de si mesmo neste ramo: não é prova.
        # OR: basta uma regra cuja conclusão seja o alvo.
        for r in indice[alvo]:
            met["regras_tentadas"] += 1
            premissas = []
            # AND: todas as premissas da regra precisam ser provadas.
            for p in r.premissas:
                prova = provar(p, ancestrais | {alvo})
                if prova is None:
                    break
                premissas.append(prova)
            else:  # Executa apenas se nenhuma premissa falhou.
                cache[alvo] = {"regra": r.nome, "conclusao": alvo, "premissas": premissas}
                return cache[alvo]
        return None
    prova = provar(consulta, set())
    return prova, met


def cenarios():
    """Conjuntos de fatos observados: falhas típicas, caso normal e casos-limite."""
    return {
        "cabo": {"sem_link", "cabo_danificado"},
        "dhcp": {"link_ativo", "sem_ip", "dhcp_inativo"},
        "dns": {"ip_valido", "gateway_responde", "dns_falha"},
        "gateway": {"ip_valido", "gateway_falha", "outros_afetados"},
        "servico": {"ip_valido", "gateway_responde", "dns_responde", "servico_falha"},
        "normal": {"ip_valido", "gateway_responde", "dns_responde", "servico_responde"},
        "incompleto": {"link_ativo"},
        "conflitante": {"ip_valido", "gateway_responde", "dns_responde", "dns_falha"},
        "coletivo": {"sem_link", "cabo_danificado", "outros_afetados"},
    }


def executar():
    registros = []
    for nome, fatos in cenarios().items():
        conhecidos, provas, met = frente(fatos)
        consultas = []
        # Os dois motores respondem à mesma consulta para conferência cruzada.
        for q in CONSULTAS:
            prova, m = tras(q, fatos)
            consultas.append({"consulta": q, "frente": q in conhecidos,
                              "tras": prova is not None, "prova": prova, "metricas": m})
        registros.append({"cenario": nome, "fatos": sorted(fatos),
                          "derivados": sorted(conhecidos-fatos), "metricas_frente": met,
                          "consultas": consultas, "provas_frente": provas})
    dados = {"regras": [asdict(r) for r in REGRAS], "execucoes": registros}
    salvar("p06", dados)
    plt = plotar()
    fig, ax = plt.subplots(figsize=(10, 4.3))
    matriz = [[int(q["frente"]) for q in r["consultas"]] for r in registros]
    from matplotlib.colors import ListedColormap
    ax.imshow(matriz, cmap=ListedColormap(["#edf1f5", "#158b7d"]), vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(range(len(registros)), [r["cenario"] for r in registros], fontsize=10.5)
    ax.set_xticks(range(len(CONSULTAS)), [q.replace("_", "\n") for q in CONSULTAS], fontsize=10.5)
    for i, linha in enumerate(matriz):
        for j, v in enumerate(linha):
            ax.text(j, i, "Sim" if v else "?", ha="center", va="center", color="white" if v else "#617385", fontsize=10.5)
    ax.set_title("Consultas provadas (Sim) e sem prova (?): ausência não equivale a falsidade")
    fig.tight_layout(); fig.savefig(FIGURAS / "p06_consultas.png", dpi=220); plt.close(fig)
    return dados


if __name__ == "__main__":
    executar()
