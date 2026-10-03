"""Projeto 2: evacuação em corredores de custo unitário; BFS, DFS e IDDFS."""

from collections import deque
import random
from time import perf_counter
from .comum import vizinhos, caminho, salvar, plotar, FIGURAS, desenhar_mapa


def corredores(comprimento):
    """Duas rotas entre os mesmos pontos: atalho de 4 passos e volta longa.

    A família permite variar o tamanho com controle do ótimo conhecido. É um
    modelo abstrato de corredores, não uma planta real da universidade.
    """
    # Linhas 0 e 2 abertas, ligadas apenas nas duas extremidades da linha 1.
    grade = [[0]*comprimento for _ in range(3)]
    grade[0] = [1]*comprimento
    grade[2] = [1]*comprimento
    grade[1][0] = grade[1][-1] = 1
    return grade, (0, 0), (0, 4)


def labirinto(semente, altura=11, largura=15):
    """Labirinto perfeito: uma árvore de corredores criada por DFS aleatório.

    Usado como segunda família de avaliação. Há bifurcações e becos sem saída,
    mas uma única rota simples entre quaisquer duas células acessíveis.
    """
    rng = random.Random(semente)
    grade = [[0]*largura for _ in range(altura)]
    pilha = [(0, 0)]
    grade[0][0] = 1
    while pilha:
        r, c = pilha[-1]
        # Saltos de duas células: as células ímpares entre elas são as paredes.
        opcoes = [(r+dr, c+dc) for dr,dc in ((2,0),(0,2),(-2,0),(0,-2))
                  if 0 <= r+dr < altura and 0 <= c+dc < largura and not grade[r+dr][c+dc]]
        if not opcoes:
            pilha.pop()  # Beco sem saída: retrocede até haver célula não visitada.
            continue
        nr,nc = rng.choice(opcoes)
        # Abre a célula escolhida e a parede intermediária que a liga à atual.
        grade[(r+nr)//2][(c+nc)//2] = grade[nr][nc] = 1
        pilha.append((nr,nc))
    return grade, (0,0), (altura-1,largura-1)


def buscar(grade, inicio, objetivo, metodo="bfs"):
    """Busca sem heurística: BFS (fila), DFS (pilha) ou IDDFS (limites crescentes).

    BFS e DFS compartilham o laço e diferem só na ponta de onde a fronteira é
    retirada. IDDFS repete uma DFS limitada, guardando apenas a trilha atual.
    """
    if metodo not in {"bfs", "dfs", "iddfs"}:
        raise ValueError("Método desconhecido")
    t0 = perf_counter()
    expandidos, gerados, pico = 0, 0, 0
    rota = []
    if metodo in {"bfs", "dfs"}:
        fronteira = deque([inicio])
        pais = {inicio: None}
        gerados, pico = 1, 1
        while fronteira:
            # FIFO explora por camadas (ótimo em passos); LIFO aprofunda primeiro.
            atual = fronteira.popleft() if metodo == "bfs" else fronteira.pop()
            expandidos += 1
            if atual == objetivo:
                rota = caminho(pais, atual)
                break
            sucessores = list(vizinhos(grade, atual))
            if metodo == "dfs":
                sucessores.reverse()  # A pilha também visita 'baixo' primeiro.
            for prox in sucessores:
                if prox not in pais:
                    pais[prox] = atual  # Visitado ao inserir: evita duplicação.
                    fronteira.append(prox)
                    gerados += 1
            pico = max(pico, len(fronteira))
    else:
        def limitada(atual, limite, trilha, presentes):
            nonlocal expandidos, gerados, pico
            expandidos += 1
            pico = max(pico, len(trilha))
            if atual == objetivo:
                return list(trilha)
            if limite == 0:
                return None
            for prox in vizinhos(grade, atual):
                # Só a trilha corrente é checada: evita ciclos com memória O(d).
                if prox not in presentes:
                    gerados += 1
                    presentes.add(prox); trilha.append(prox)
                    resultado = limitada(prox, limite-1, trilha, presentes)
                    # Desfaz a escolha para que outro ramo possa usar a célula.
                    trilha.pop(); presentes.remove(prox)
                    if resultado is not None:
                        return resultado
            return None
        # Em um grafo finito, qualquer caminho simples tem até |V|-1 arestas.
        for limite in range(sum(bool(v) for linha in grade for v in linha)):
            gerados += 1
            rota = limitada(inicio, limite, [inicio], {inicio})
            if rota is not None:
                break
        rota = rota or []
    return {"metodo": metodo, "caminho": rota, "passos": len(rota)-1 if rota else None,
            "expandidos": expandidos, "gerados": gerados, "pico_estrutura": pico,
            "tempo_ms": (perf_counter()-t0)*1000}


def executar():
    registros = []
    # Família 1: o ótimo é sempre 4 passos; cresce apenas a rota alternativa.
    for n in (10, 20, 40, 80):
        grade, inicio, objetivo = corredores(n)
        for metodo in ("bfs", "dfs", "iddfs"):
            r = buscar(grade, inicio, objetivo, metodo)
            r["comprimento"] = n
            r["cenario"] = "corredores"
            registros.append(r)
    # Família 2: labirintos com caminho único, onde os três devem concordar.
    for seed in range(10):
        grade, inicio, objetivo = labirinto(seed)
        for metodo in ("bfs", "dfs", "iddfs"):
            r = buscar(grade, inicio, objetivo, metodo)
            r.update(semente=seed, cenario="labirinto")
            registros.append(r)
    dados = {"execucoes": registros, "custos_unitarios": True}
    salvar("p02", dados)
    plt = plotar()
    fig, axs = plt.subplots(3, 1, figsize=(9, 4))
    for ax, metodo in zip(axs, ("bfs", "dfs", "iddfs")):
        r = next(r for r in registros if r.get("comprimento") == 20 and r["metodo"] == metodo)
        desenhar_mapa(ax, corredores(20)[0], r["caminho"], f"{metodo.upper()}: {r['passos']} passos")
        # A rotina comum marca o canto oposto; reposicionamos o destino real.
        ax.collections[-1].remove()
        ax.scatter([0, 4], [0, 0], c=["#15966d", "#db3454"], s=40)
    fig.tight_layout(); fig.savefig(FIGURAS / "p02_corredores.png", dpi=220); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 3))
    for metodo in ("bfs", "dfs", "iddfs"):
        rs = [r for r in registros if r["metodo"] == metodo and r["cenario"] == "corredores"]
        ax.plot([r["comprimento"] for r in rs], [r["expandidos"] for r in rs], "o-", label=metodo.upper())
    ax.set(xlabel="Comprimento do corredor", ylabel="Expansões", title="Custo de busca e ordem dos sucessores")
    ax.legend(); fig.tight_layout(); fig.savefig(FIGURAS / "p02_expansoes.png", dpi=220); plt.close(fig)
    return dados


if __name__ == "__main__":
    executar()
