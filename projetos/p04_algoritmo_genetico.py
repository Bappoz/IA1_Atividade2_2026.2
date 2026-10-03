"""Projeto 4: escolher equipamentos de campo sob limites de massa e volume.

AG binário com torneio, cruzamento uniforme, mutação, reparo e elitismo.
Programação dinâmica bidimensional fornece um ótimo exato independente.
"""

import random
import statistics
from dataclasses import dataclass, asdict
from .comum import salvar, plotar, FIGURAS


@dataclass(frozen=True)
class Item:
    nome: str
    massa: int
    volume: int
    utilidade: int


def instancia():
    """24 itens sintéticos com massa, volume e utilidade sorteados (semente fixa)."""
    nomes = ["multimetro", "sensor CO2", "camera", "tripé", "bateria", "roteador",
             "luximetro", "decibelimetro", "drone", "GNSS", "anemometro", "termometro",
             "kit solo", "tablet", "radio", "painel solar", "cabos", "microscopio",
             "sensor agua", "gravador", "balanca", "osciloscopio", "estacao meteo", "notebook"]
    rng = random.Random(2026)
    return [Item(n, rng.randint(3, 16), rng.randint(2, 12), rng.randint(12, 60)) for n in nomes]


def medidas(bits, itens):
    """Massa, volume e utilidade totais dos itens marcados com bit 1."""
    return tuple(sum(getattr(i, campo)*b for i, b in zip(itens, bits))
                 for campo in ("massa", "volume", "utilidade"))


def reparar(bits, itens, limites):
    """Remove a menor utilidade por recurso normalizado até obter viabilidade.

    A escolha é determinística. Reparo evita premiar cargas inviáveis, mas
    introduz viés e não transforma o AG em método exato de otimização.
    """
    bits = list(bits)
    while True:
        massa, volume, _ = medidas(bits, itens)
        if massa <= limites[0] and volume <= limites[1]:
            return tuple(bits)
        ativos = [j for j, b in enumerate(bits) if b]
        # Dividir pelos limites põe massa e volume na mesma escala (fração usada).
        pior = min(ativos, key=lambda j: (itens[j].utilidade /
                   (itens[j].massa/limites[0]+itens[j].volume/limites[1]), j))
        bits[pior] = 0


def exato(itens, limites):
    """Mochila 0/1 com duas capacidades, O(n*M*V) tempo e O(M*V) estados.

    Capacidades são percorridas em ordem decrescente para que o item atual
    não seja reutilizado. Um bitmask preserva a seleção que alcançou o valor.
    """
    M, V = limites
    # dp[m][v] = (melhor utilidade com massa <= m e volume <= v, itens usados).
    dp = [[(0, 0) for _ in range(V+1)] for _ in range(M+1)]
    for j, item in enumerate(itens):
        for m in range(M, item.massa-1, -1):
            for v in range(V, item.volume-1, -1):
                anterior, mask = dp[m-item.massa][v-item.volume]
                candidato = anterior+item.utilidade
                if candidato > dp[m][v][0]:
                    dp[m][v] = (candidato, mask | (1 << j))
    valor, mask = dp[M][V]
    bits = tuple(int(bool(mask & (1 << j))) for j in range(len(itens)))
    return valor, bits


def genetico(itens, limites, semente, populacao=80, geracoes=120, mutacao=None):
    """AG geracional: cromossomo binário, um gene por item (1 = levar).

    mutacao=None usa 1/n (em média um bit trocado por filho); mutacao=0 é a
    ablação usada para medir quanto a mutação contribui para o resultado.
    """
    rng = random.Random(semente)
    n = len(itens)
    taxa = 1/n if mutacao is None else mutacao
    # Como todo indivíduo é reparado, a aptidão é a própria utilidade, sem penalidade.
    def fitness(bits):
        return medidas(bits, itens)[2]
    # População inicial aleatória, já tornada viável pelo reparo.
    pop = [reparar([rng.randrange(2) for _ in itens], itens, limites) for _ in range(populacao)]
    historico = []
    # Há geracoes transições e geracoes+1 medições, incluindo geração zero.
    for g in range(geracoes+1):
        pop.sort(key=fitness, reverse=True)
        historico.append(fitness(pop[0]))
        if g == geracoes:
            break
        nova = pop[:2]  # Elitismo conserva dois indivíduos, inclusive o melhor.
        while len(nova) < populacao:
            # Torneio de tamanho 3: o melhor de três sorteados vira pai.
            pais = [max(rng.sample(pop, 3), key=fitness) for _ in range(2)]
            # Cruzamento uniforme: cada gene vem de um dos pais com chance 1/2.
            filho = [pais[rng.randrange(2)][j] for j in range(n)]
            # Mutação bit a bit: inverte o gene com probabilidade taxa.
            for j in range(n):
                if rng.random() < taxa:
                    filho[j] ^= 1
            nova.append(reparar(filho, itens, limites))
        pop = nova
    return {"semente": semente, "valor": historico[-1], "bits": pop[0], "historico": historico}


def executar():
    itens, limites = instancia(), (65, 48)
    otimo, bits = exato(itens, limites)
    # Mesmas 30 sementes nas duas configurações: a única diferença é a mutação.
    registros =[genetico(itens, limites, seed) for seed in range(30)]
    ablac = [genetico(itens, limites, seed, mutacao=0) for seed in range(30)]
    dados = {"itens": [asdict(i) for i in itens], "limites": limites,
             "parametros": {"populacao": 80, "geracoes": 120, "elitismo": 2,
                            "torneio": 3, "mutacao": 1/len(itens)},
             "otimo": otimo, "bits_otimos": bits, "execucoes": registros, "sem_mutacao": ablac}
    salvar("p04", dados)
    plt = plotar()
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.5))
    for rs, label, color in ((registros, "AG completo", "#137f77"), (ablac, "Sem mutação", "#d57836")):
        medias = [statistics.mean(r["historico"][g] for r in rs) for g in range(121)]
        desvios = [statistics.pstdev(r["historico"][g] for r in rs) for g in range(121)]
        axs[0].plot(medias, label=label, color=color)
        axs[0].fill_between(range(121), [m-d for m,d in zip(medias,desvios)],
                            [m+d for m,d in zip(medias,desvios)], alpha=.14, color=color)
    axs[0].axhline(otimo, color="#374151", linestyle="--", label=f"Ótimo exato: {otimo}")
    axs[0].set(xlabel="Geração", ylabel="Melhor utilidade", title="Média ± desvio padrão (30 sementes)")
    axs[0].legend(fontsize=10)
    axs[1].boxplot([[r["valor"] for r in registros], [r["valor"] for r in ablac]],
                   tick_labels=["Completo", "Sem mutação"])
    axs[1].axhline(otimo, color="#374151", linestyle="--")
    axs[1].set(ylabel="Utilidade final", title="Dispersão entre execuções")
    fig.tight_layout(); fig.savefig(FIGURAS / "p04_convergencia.png", dpi=220); plt.close(fig)
    return dados


if __name__ == "__main__":
    executar()
