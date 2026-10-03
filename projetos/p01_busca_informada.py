"""Projeto 1: rotas de entrega com custo de terreno; A*, UCS e gulosa.

Execute: python -m projetos.p01_busca_informada
As bibliotecas heapq e itertools fornecem estruturas, não solucionadores.
"""

import heapq
from itertools import count
from time import perf_counter

from .comum import mapa, vizinhos, caminho, salvar, plotar, FIGURAS, desenhar_mapa


def buscar(grade, inicio, objetivo, metodo="astar"):
    """Busca em grafo com relaxamento e descarte de entradas obsoletas.

    A* ordena por g+h; UCS (Dijkstra) por g; gulosa por h. h é Manhattan
    multiplicada pelo menor custo positivo do mapa, portanto admissível e
    consistente para esta vizinhança. Empates seguem a ordem de inserção.
    """
    if metodo not in {"astar", "ucs", "gulosa"}:
        raise ValueError("Método desconhecido")
    # Escalar a Manhattan pelo menor custo do mapa impede a superestimação:
    # nenhum passo custa menos que isso, então h nunca passa do custo real.
    menor = min(v for linha in grade for v in linha if v > 0)
    def h(s):
        return menor * (abs(s[0]-objetivo[0]) + abs(s[1]-objetivo[1]))
    # A única diferença entre os três métodos é a chave de ordenação do heap.
    def prioridade(s, g):
        return g+h(s) if metodo == "astar" else g if metodo == "ucs" else h(s)
    # O contador desempata prioridades iguais sem comparar as tuplas de estado.
    seq = count()
    fronteira = [(prioridade(inicio, 0), next(seq), 0, inicio)]
    # custos guarda o melhor g conhecido; pais permite reconstruir a rota.
    custos, pais = {inicio: 0}, {inicio: None}
    expandidos, gerados, pico = 0, 1, 1
    t0 = perf_counter()
    while fronteira:
        _, _, g, atual = heapq.heappop(fronteira)
        if g != custos[atual]:
            continue  # Uma rota melhor já substituiu esta entrada no heap.
        expandidos += 1  # Inclui o objetivo quando retirado da fronteira.
        if atual == objetivo:
            return {"metodo": metodo, "custo": g, "caminho": caminho(pais, atual),
                    "expandidos": expandidos, "gerados": gerados, "pico_fronteira": pico,
                    "tempo_ms": (perf_counter()-t0)*1000}
        for prox in vizinhos(grade, atual):
            # O custo é pago ao entrar na célula, por isso a origem é gratuita.
            novo = g + grade[prox[0]][prox[1]]
            # Relaxamento: só reinsere quando a nova rota é estritamente melhor.
            if novo < custos.get(prox, float("inf")):
                custos[prox], pais[prox] = novo, atual
                heapq.heappush(fronteira, (prioridade(prox, novo), next(seq), novo, prox))
                gerados += 1
        pico = max(pico, len(fronteira))
    # Fronteira esgotada sem atingir o objetivo: não existe rota.
    return {"metodo": metodo, "custo": None, "caminho": [], "expandidos": expandidos,
            "gerados": gerados, "pico_fronteira": pico, "tempo_ms": (perf_counter()-t0)*1000}


def executar():
    registros = []
    # Trinta ambientes: comparar apenas um labirinto favoreceria uma heurística.
    for seed in range(30):
        grade = mapa(seed)
        for metodo in ("astar", "ucs", "gulosa"):
            r = buscar(grade, (0, 0), (17, 24), metodo)
            r["semente"] = seed
            registros.append(r)
    dados = {"altura": 18, "largura": 25, "sementes": list(range(30)), "execucoes": registros}
    salvar("p01", dados)
    plt = plotar()
    # Figura 1: as três rotas no mesmo mapa (semente 0) para comparação visual.
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.3))
    for ax, metodo in zip(axs, ("astar", "ucs", "gulosa")):
        r = next(r for r in registros if r["semente"] == 0 and r["metodo"] == metodo)
        desenhar_mapa(ax, mapa(0), r["caminho"], f"{metodo.upper()} | custo {r['custo']} | {r['expandidos']} nós")
    fig.suptitle("Entrega no campus: paredes escuras; azul mais escuro = maior custo")
    fig.tight_layout()
    fig.savefig(FIGURAS / "p01_rotas.png", dpi=220)
    plt.close(fig)
    # Figura 2: distribuição das expansões nos 30 mapas, não um caso isolado.
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.boxplot([[r["expandidos"] for r in registros if r["metodo"] == m]
                for m in ("astar", "ucs", "gulosa")], tick_labels=["A*", "UCS", "Gulosa"])
    ax.set(ylabel="Nós expandidos", title="Distribuição em 30 mapas independentes")
    fig.tight_layout(); fig.savefig(FIGURAS / "p01_expansoes.png", dpi=220); plt.close(fig)
    return dados


if __name__ == "__main__":
    executar()
