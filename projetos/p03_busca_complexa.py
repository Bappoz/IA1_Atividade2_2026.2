"""Projeto 3: planejamento AND-OR de um robô sob desvio não determinístico.

Um estado é (local, bateria). O robô escolhe uma ação (OR); o ambiente pode
produzir QUALQUER resultado dessa ação (AND). Procuramos uma política forte,
com chegada garantida e menor tempo no pior caso. O grafo deste domínio é
acíclico; não são resolvidas políticas cíclicas nem observabilidade parcial.
"""

from dataclasses import dataclass
from functools import lru_cache
from math import inf, isfinite
from .comum import salvar, plotar, FIGURAS


@dataclass(frozen=True)
class Acao:
    nome: str
    tempo: int
    resultados: tuple  # Pares (local seguinte, energia consumida).


# Modelo do domínio: local -> ações disponíveis. Ação com mais de um resultado
# é não determinística; o planejador não escolhe qual deles ocorre.
ACOES = {
    "Portaria": (Acao("atalho", 2, (("Atrio", 2), ("Desvio", 7))),
                 Acao("via segura", 4, (("Biblioteca", 2),))),
    "Atrio": (Acao("ponte", 2, (("Passarela", 2), ("Patio", 4))),
              Acao("rampa", 5, (("Passarela", 1),))),
    "Desvio": (Acao("escada", 3, (("Patio", 2),)),),
    "Biblioteca": (Acao("elevador", 2, (("Passarela", 2), ("Patio", 3))),
                   Acao("contorno", 5, (("Patio", 1),))),
    "Passarela": (Acao("entrega", 3, (("Laboratorio", 2),)),),
    "Patio": (Acao("normal", 4, (("Laboratorio", 2),)),
              Acao("expresso", 2, (("Laboratorio", 4),))),
    "Laboratorio": (),
}


def planejar(bateria, robusto=True, acoes=None):
    """Programação dinâmica sobre a árvore AND-OR, com memoização de estados.

    V(s)=min_a [tempo(a)+max_o V(resultado(s,a,o))]. Estado sem energia tem
    valor infinito. Todos os resultados devem ser viáveis para uma ação forte.
    A versão otimista troca max por min: serve de controle que ignora riscos.
    """
    acoes = ACOES if acoes is None else acoes
    politica, avaliados = {}, []
    # O cache evita reavaliar o mesmo (local, energia) alcançado por ramos diferentes.
    @lru_cache(None)
    def valor(local, energia):
        avaliados.append((local, energia))
        if energia < 0:
            return inf  # Bateria esgotada: estado perdedor.
        if local == "Laboratorio":
            return 0  # Objetivo: nenhum tempo adicional.
        melhor = inf
        # Nó OR: o robô escolhe a ação de menor valor.
        for acao in acoes.get(local, ()):
            # Nó AND: todos os resultados possíveis da ação são avaliados.
            filhos = [valor(destino, energia-consumo) for destino, consumo in acao.resultados]
            # max = pior caso (basta um filho infinito para descartar a ação).
            candidato = acao.tempo + (max(filhos) if robusto else min(filhos))
            if candidato < melhor:
                melhor = candidato
                politica[(local, energia)] = acao
        return melhor
    v = valor("Portaria", bateria)
    return {"valor": v, "politica": politica, "avaliados": len(avaliados)}


def avaliar_politica(politica, estado):
    """Enumera TODOS os desfechos; mede garantia sem amostragem aleatória.

    Retorna uma lista de (sucesso, tempo, trilha). Uma política otimista pode
    não definir ação para estados perdedores, explicitamente marcados falhos.
    """
    local, energia = estado
    if energia < 0:
        return [(False, 0, [estado])]
    if local == "Laboratorio":
        return [(True, 0, [estado])]
    acao = politica.get(estado)
    if acao is None:
        return [(False, 0, [estado])]
    trajetorias = []
    # Produto dos ramos: cada resultado da ação gera suas próprias trajetórias.
    for destino, consumo in acao.resultados:
        for sucesso, tempo, trilha in avaliar_politica(politica, (destino, energia-consumo)):
            trajetorias.append((sucesso, acao.tempo+tempo, [estado]+trilha))
    return trajetorias


def executar():
    registros = []
    # Quatro capacidades: da insuficiente à folgada, com e sem tratamento do risco.
    for bateria in (4, 6, 8, 11):
        for robusto in (True, False):
            r = planejar(bateria, robusto)
            trajetorias = avaliar_politica(r["politica"], ("Portaria", bateria))
            registros.append({"bateria": bateria, "metodo": "AND-OR" if robusto else "otimista",
                              "valor": r["valor"] if isfinite(r["valor"]) else None,
                              "estados_avaliados": r["avaliados"],
                              "garantia": all(t[0] for t in trajetorias),
                              "desfechos": [{"sucesso": s, "tempo": t, "trilha": p} for s, t, p in trajetorias],
                              "politica": [{"local": s[0], "energia": s[1], "acao": a.nome}
                                           for s, a in sorted(r["politica"].items())]})
    dados = {"modelo": {k: [{"nome": a.nome, "tempo": a.tempo, "resultados": a.resultados}
                             for a in v] for k, v in ACOES.items()}, "execucoes": registros}
    salvar("p03", dados)
    plt = plotar()
    fig, ax = plt.subplots(figsize=(9, 3.7))
    r = planejar(8)
    # Desenha apenas estados alcançáveis pela política, não o cache completo.
    trajetorias = avaliar_politica(r["politica"], ("Portaria", 8))
    coords = {("Portaria", 8): (0, 0), ("Biblioteca", 6): (1, 0),
              ("Passarela", 4): (2, 1), ("Patio", 3): (2, -1),
              ("Laboratorio", 2): (3, 1), ("Laboratorio", 1): (3, -1)}
    arestas = {(trilha[i], trilha[i+1]) for _, _, trilha in trajetorias for i in range(len(trilha)-1)}
    caixas = {}
    for estado, (x, y) in coords.items():
        acao = r["politica"].get(estado)
        label = f"{estado[0]}\nbateria={estado[1]}" + (f"\n{acao.nome}: {acao.tempo} min" if acao else "\nOBJETIVO")
        caixas[estado] = ax.text(x, y, label, ha="center", va="center", fontsize=9,
                bbox={"boxstyle": "round,pad=.55", "fc": "#e9f3f1" if not acao else "#edf2f7", "ec": "#658397"})
    for origem, destino in sorted(arestas):
        x, y = coords[origem]; xx, yy = coords[destino]
        # Recortar nas caixas preserva as pontas das setas fora dos textos.
        ax.annotate("", (xx, yy), (x, y), arrowprops={
            "arrowstyle": "->", "color": "#667b8a",
            "patchA": caixas[origem].get_bbox_patch(),
            "patchB": caixas[destino].get_bbox_patch(), "shrinkA": 3, "shrinkB": 3})
    ax.set(xlim=(-.45, 3.5), ylim=(-1.7, 1.7), title="Política forte com bateria 8: todos os ramos chegam ao laboratório")
    ax.axis("off"); fig.tight_layout(); fig.savefig(FIGURAS / "p03_politica.png", dpi=220); plt.close(fig)
    return dados


if __name__ == "__main__":
    executar()
