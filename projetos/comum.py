"""Infraestrutura de saída e mapas; não implementa algoritmos de IA."""

import json
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RESULTADOS = RAIZ / "resultados"
FIGURAS = RESULTADOS / "figuras"


def salvar(nome, dados):
    """JSON conserva inclusive trajetórias, parâmetros e sementes."""
    RESULTADOS.mkdir(exist_ok=True)
    (RESULTADOS / f"{nome}.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def plotar():
    """Backend sem janela: funciona em máquinas sem ambiente gráfico."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIGURAS.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 140})
    return plt


def mapa(semente, altura=18, largura=25, ponderado=True):
    """Instância sintética. Zero = parede; demais valores = custo de entrada.

    A borda superior e a direita são abertas para garantir conectividade entre
    origem e destino, sem pressupor que esse corredor seja uma rota ótima.
    """
    # Gerador local: a mesma semente sempre reproduz o mesmo mapa.
    rng = random.Random(semente)
    # 23% de paredes; custo 1 é três vezes mais provável que os demais.
    grade = [[0 if rng.random() < .23 else
              (rng.choice([1, 1, 1, 2, 4, 7]) if ponderado else 1)
              for _ in range(largura)] for _ in range(altura)]
    for c in range(largura):
        if grade[0][c] == 0:
            grade[0][c] = rng.choice([1, 1, 2, 4, 7]) if ponderado else 1
    for r in range(altura):
        if grade[r][-1] == 0:
            grade[r][-1] = rng.choice([1, 1, 2, 4, 7]) if ponderado else 1
    return grade


def vizinhos(grade, estado):
    """Ordem fixa: baixo, direita, cima, esquerda; sem movimentos diagonais."""
    r, c = estado
    for dr, dc in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grade) and 0 <= nc < len(grade[0]) and grade[nr][nc]:
            yield nr, nc


def caminho(pais, destino):
    """Reconstrói a rota seguindo os pais do destino até a origem (pai None)."""
    rota = []
    while destino is not None:
        rota.append(destino)
        destino = pais[destino]
    return rota[::-1]


def desenhar_mapa(ax, grade, rota, titulo):
    """Desenha paredes, faixas de custo, a rota e os marcadores de origem/destino."""
    from matplotlib.colors import ListedColormap, BoundaryNorm
    # Faixas discretas: parede (0) e custos 1, 2, 4 e 7 em tons crescentes.
    cmap = ListedColormap(["#263344", "#eef2f5", "#c6d9e7", "#88aeca", "#467a9e"])
    norm = BoundaryNorm([-.5, .5, 1.5, 3, 5, 8], cmap.N)
    ax.imshow(grade, cmap=cmap, norm=norm)
    if rota:
        ax.plot([c for r, c in rota], [r for r, c in rota], color="#e65d35", lw=2)
    ax.scatter([0, len(grade[0])-1], [0, len(grade)-1], c=["#15966d", "#db3454"], s=45)
    ax.set_title(titulo)
    ax.set_xticks([])
    ax.set_yticks([])
