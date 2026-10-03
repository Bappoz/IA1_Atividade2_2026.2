"""Verifica arquivos, paginação e consistência entre saídas e instâncias."""
import json
from pypdf import PdfReader
from projetos.comum import RAIZ, vizinhos
from projetos.p02_busca_nao_informada import corredores, labirinto
from projetos.p04_algoritmo_genetico import Item, medidas
from projetos.p05_csp import Disciplina, validar


def exigir(condicao, mensagem):
    if not condicao:
        raise ValueError(mensagem)


def main():
    ds=[json.loads((RAIZ / f"resultados/p{i:02}.json").read_text()) for i in range(1,7)]
    entradas=json.loads((RAIZ / "dados/instancias.json").read_text())
    mapas={m["semente"]:m["grade"] for m in entradas["p01"]["mapas"]}
    for r in ds[0]["execucoes"]:
        grade=mapas[r["semente"]]; rota=[tuple(s) for s in r["caminho"]]
        exigir(rota[0]==(0,0) and rota[-1]==(17,24),"P1: extremidades incorretas")
        exigir(all(b in vizinhos(grade,a) for a,b in zip(rota,rota[1:])),"P1: caminho inválido")
        exigir(sum(grade[a][b] for a,b in rota[1:])==r["custo"],"P1: custo inconsistente")
    ucs={r["semente"]:r["custo"] for r in ds[0]["execucoes"] if r["metodo"]=="ucs"}
    exigir(all(r["custo"]==ucs[r["semente"]] for r in ds[0]["execucoes"] if r["metodo"]=="astar"),"P1: A* diverge de UCS")
    for r in ds[1]["execucoes"]:
        grade,inicio,fim=corredores(r["comprimento"]) if r["cenario"]=="corredores" else labirinto(r["semente"])
        rota=[tuple(s) for s in r["caminho"]]
        exigir(rota[0]==inicio and rota[-1]==fim,"P2: extremidades incorretas")
        exigir(all(b in vizinhos(grade,a) for a,b in zip(rota,rota[1:])),"P2: caminho inválido")
        exigir(len(rota)-1==r["passos"],"P2: distância inconsistente")
    for r in ds[2]["execucoes"]:
        exigir(r["garantia"]==all(t["sucesso"] for t in r["desfechos"]),"P3: garantia inconsistente")
        if r["metodo"]=="AND-OR" and r["valor"] is not None:
            exigir(r["garantia"] and r["valor"]==max(t["tempo"] for t in r["desfechos"]),"P3: pior caso inconsistente")
    itens=[Item(**i) for i in ds[3]["itens"]]
    for r in ds[3]["execucoes"]+ds[3]["sem_mutacao"]:
        m,v,u=medidas(r["bits"],itens)
        exigir(m<=65 and v<=48 and u==r["valor"]<=ds[3]["otimo"],"P4: seleção ou utilidade inconsistente")
        exigir(all(a<=b for a,b in zip(r["historico"],r["historico"][1:])),"P4: elitismo inconsistente")
    for r in ds[4]["execucoes"]:
        if r["cenario"]=="normal":
            cursos=[Disciplina(**c) for c in ds[4]["disciplinas"]]
            exigir(validar(cursos,r["solucao"]),"P5: grade inválida")
        else:
            exigir(r["solucao"] is None,"P5: cenário impossível tem solução")
    exigir(all(q["frente"]==q["tras"] for r in ds[5]["execucoes"] for q in r["consultas"]),"P6: motores divergem")
    pdf=PdfReader(RAIZ / "output/pdf/relatorio_atividade2.pdf")
    exigir(len(pdf.pages)==18,"PDF não tem 18 páginas")
    for i,pagina in enumerate(pdf.pages):
        texto=pagina.extract_text()
        exigir(f"{i//3+1:02d} |" in texto,f"PDF: projeto ausente na página {i+1}")
        exigir(f"Projeto {i//3+1} | página {i%3+1}/3" in texto,f"PDF: paginação incorreta na página {i+1}")
        exigir("�" not in texto,"PDF: caractere inválido")
    fontes=list((RAIZ / "projetos").glob("p0*.py"))
    exigir(len(fontes)==6 and all('"""' in p.read_text() and "#" in p.read_text() for p in fontes),"Faltam projetos comentados")
    print("Entrega verificada: seis projetos, resultados consistentes e PDF com 3 páginas por projeto.")


if __name__=="__main__":
    main()
