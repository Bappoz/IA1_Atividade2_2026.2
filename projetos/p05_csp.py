"""Projeto 5: alocação de disciplinas em salas/horários com CSP binário.

Comparação: backtracking simples versus MRV + grau + LCV + MAC (AC-3 a
cada atribuição). Domínios já aplicam capacidade, equipamento e disponibilidade.
"""

from collections import deque
from dataclasses import dataclass, asdict
from time import perf_counter
from .comum import salvar, plotar, FIGURAS


@dataclass(frozen=True)
class Disciplina:
    nome: str
    docente: str
    grupos: tuple
    alunos: int
    computadores: bool
    horarios: tuple = (0, 1, 2, 3, 4)


# Sala -> (capacidade, possui computadores).
SALAS = {"Lab40": (40, True), "Lab24": (24, True), "Aud60": (60, False)}
HORARIOS = ["Seg 08h", "Seg 10h", "Ter 08h", "Ter 10h", "Qua 08h"]


def instancia():
    return [Disciplina("IA", "Lia", ("A",), 32, True, (0, 1, 2)),
            Disciplina("Redes", "Beto", ("A",), 32, True, (0, 1, 3)),
            Disciplina("BD", "Lia", ("B",), 22, True, (1, 2, 3)),
            Disciplina("Compiladores", "Nina", ("B",), 22, True),
            Disciplina("Grafos", "Beto", ("B",), 22, False),
            Disciplina("Calculo", "Ivo", ("A", "C"), 54, False, (0, 2, 4)),
            Disciplina("IHC", "Nina", ("A",), 32, False),
            Disciplina("Fisica", "Ivo", ("B",), 22, False),
            Disciplina("Embarcados", "Lia", ("C",), 20, True),
            Disciplina("Eletronica", "Beto", ("C",), 20, True),
            Disciplina("Projeto", "Nina", ("C",), 20, False),
            Disciplina("Estatistica", "Ivo", ("C",), 20, False)]


def dominios(disciplinas):
    """Valores (horário, sala) que já respeitam as restrições unárias.

    Capacidade, equipamento e disponibilidade dependem de uma só disciplina,
    então são filtrados aqui em vez de serem testados durante a busca.
    """
    return {d.nome: [(h, s) for h in d.horarios for s, (cap, comp) in SALAS.items()
                     if cap >= d.alunos and (not d.computadores or comp)] for d in disciplinas}


def compativel(a, va, b, vb):
    """Não compartilhar sala, docente ou grupo de estudantes simultaneamente."""
    if va[0] != vb[0]:
        return True  # Horários diferentes nunca conflitam.
    return va[1] != vb[1] and a.docente != b.docente and not set(a.grupos).intersection(b.grupos)


def resolver(disciplinas, otimizado=True):
    """Backtracking cronológico; com otimizado=True usa MRV, grau, LCV e MAC.

    Variáveis são disciplinas e valores são pares (horário, sala). As métricas
    contam nós, tentativas, retrocessos e trabalho de propagação.
    """
    cadastro ={d.nome: d for d in disciplinas}
    dom = dominios(disciplinas)
    nomes = list(cadastro)
    # Uma aresta só é necessária se houver pelo menos um par proibido.
    adj = {a: [b for b in nomes if b != a and any(
        not compativel(cadastro[a], va, cadastro[b], vb) for va in dom[a] for vb in dom[b])]
        for a in nomes}
    met = {"nos": 0, "tentativas": 0, "backtracks": 0,
           "revisoes": 0, "removidos": 0, "verificacoes": 0}
    t0 = perf_counter()
    def permite(a, va, b, vb):
        met["verificacoes"] += 1
        return compativel(cadastro[a], va, cadastro[b], vb)
    def ac3(ds, fila):
        """Remove valores sem suporte no vizinho e reexamina arcos afetados."""
        fila = deque(fila)
        while fila:
            a, b = fila.popleft()
            met["revisoes"] += 1
            # Mantém em a só os valores com algum valor compatível em b.
            novos = [va for va in ds[a] if any(permite(a, va, b, vb) for vb in ds[b])]
            if len(novos) != len(ds[a]):
                met["removidos"] += len(ds[a])-len(novos)
                ds[a] = novos
                if not novos:
                    return False  # Domínio vazio: o ramo atual é inviável.
                # O domínio de a encolheu: seus outros vizinhos podem perder suporte.
                fila.extend((c, a) for c in adj[a] if c != b)
        return True
    def bt(atribuicao, ds):
        met["nos"] += 1
        if len(atribuicao) == len(nomes):
            return dict(atribuicao)
        livres = [v for v in nomes if v not in atribuicao]
        if otimizado:
            # MRV; empates favorecem a variável com maior grau restante.
            var = min(livres, key=lambda v: (len(ds[v]), -sum(n in livres for n in adj[v]), v))
            # LCV: testa primeiro o valor que elimina menos opções dos vizinhos.
            def impacto(valor):
                return sum(not permite(var, valor, n, vn) for n in adj[var]
                           if n in livres and n != var for vn in ds[n])
            valores = sorted(ds[var], key=lambda v: (impacto(v), v))
        else:
            # Linha de base: ordem de declaração, sem nenhuma heurística.
            var, valores = livres[0], ds[livres[0]]
        for valor in valores:
            met["tentativas"] += 1
            if all(permite(var, valor, n, vn) for n, vn in atribuicao.items()):
                atribuicao[var] = valor
                # Copiar os domínios torna o rollback explícito e correto.
                novos = {v: list(d) for v, d in ds.items()}
                novos[var] = [valor]
                # MAC: propaga a atribuição pelos arcos que apontam para var.
                if not otimizado or ac3(novos, [(n, var) for n in adj[var]]):
                    solucao = bt(atribuicao, novos)
                    if solucao is not None:
                        return solucao
                del atribuicao[var]
        met["backtracks"] += 1
        return None
    # Um domínio vazio após os filtros unários já prova a inviabilidade.
    viavel = all(dom.values())
    # Pré-processamento: consistência de arco no problema inteiro antes da busca.
    if viavel and otimizado:
        viavel = ac3(dom, [(a, b) for a in nomes for b in adj[a]])
    solucao = bt({}, dom) if viavel else None
    met["tempo_ms"] = (perf_counter()-t0)*1000
    return {"metodo": "MRV+LCV+MAC" if otimizado else "backtracking", "solucao": solucao,
            "metricas": met, "dominios_iniciais": {k: len(v) for k, v in dominios(disciplinas).items()}}


def validar(disciplinas, solucao):
    """Validador independente da propagação e da busca."""
    if solucao is None or set(solucao) != {d.nome for d in disciplinas}:
        return False
    ds = dominios(disciplinas)
    if any(tuple(solucao[d.nome]) not in ds[d.nome] for d in disciplinas):
        return False
    return all(compativel(a, solucao[a.nome], b, solucao[b.nome])
               for i, a in enumerate(disciplinas) for b in disciplinas[i+1:])


def executar():
    cursos = instancia()
    # Seis aulas do mesmo professor em cinco horários: princípio da casa dos pombos.
    impossivel = [Disciplina(f"Extra{i}", "Unico", (str(i),), 32, True) for i in range(6)]
    registros = []
    for nome, ds in (("normal", cursos), ("inviavel", impossivel)):
        for otimizado in (False, True):
            r = resolver(ds, otimizado)
            r["cenario"] = nome
            r["validada"] = validar(ds, r["solucao"]) if r["solucao"] is not None else None
            registros.append(r)
    dados = {"disciplinas": [asdict(d) for d in cursos], "salas": SALAS, "horarios": HORARIOS,
             "inviavel": [asdict(d) for d in impossivel], "execucoes": registros}
    salvar("p05", dados)
    plt = plotar()
    r = next(r for r in registros if r["cenario"] == "normal" and r["metodo"] != "backtracking")
    fig, ax = plt.subplots(figsize=(10, 3.5))
    celulas = [["" for _ in HORARIOS] for _ in SALAS]
    for nome, (h, s) in r["solucao"].items():
        d = next(d for d in cursos if d.nome == nome)
        celulas[list(SALAS).index(s)][h] = f"{nome}\n{d.docente} | {','.join(d.grupos)}"
    ax.axis("off")
    tabela = ax.table(cellText=celulas, rowLabels=list(SALAS), colLabels=HORARIOS, cellLoc="center", loc="center")
    tabela.auto_set_font_size(False); tabela.set_fontsize(11); tabela.scale(1, 3.1)
    for (row, col), cell in tabela.get_celld().items():
        cell.set_edgecolor("#d4dee6")
        cell.set_facecolor("#dbeae8" if row == 0 or col == -1 else "#f3f6f9")
    ax.set_title("Grade encontrada pelo CSP: 12 disciplinas sem conflitos", pad=20)
    fig.tight_layout(); fig.savefig(FIGURAS / "p05_grade.png", dpi=220); plt.close(fig)
    return dados


if __name__ == "__main__":
    executar()
