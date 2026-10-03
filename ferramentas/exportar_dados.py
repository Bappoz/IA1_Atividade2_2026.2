"""Exporta as instâncias usadas para que possam ser inspecionadas sem gráficos."""
import json
from projetos.comum import RAIZ, mapa
from projetos.p02_busca_nao_informada import corredores, labirinto


def main():
    ds = [json.loads((RAIZ / f"resultados/p{i:02}.json").read_text()) for i in range(1,7)]
    entradas={
        "p01": {"inicio":[0,0],"objetivo":[17,24],"mapas":[{"semente":s,"grade":mapa(s)} for s in range(30)]},
        "p02": {"corredores":[{"comprimento":n,"grade":corredores(n)[0],"inicio":[0,0],"objetivo":[0,4]} for n in (10,20,40,80)],
                "labirintos":[{"semente":s,"grade":labirinto(s)[0],"inicio":[0,0],"objetivo":[10,14]} for s in range(10)]},
        "p03": {"acoes":ds[2]["modelo"],"baterias":[4,6,8,11]},
        "p04": {k:ds[3][k] for k in ("itens","limites","parametros")},
        "p05": {k:ds[4][k] for k in ("disciplinas","salas","horarios","inviavel")},
        "p06": {"regras":ds[5]["regras"],"cenarios":[{"nome":r["cenario"],"fatos":r["fatos"]} for r in ds[5]["execucoes"]]},
    }
    arquivo=RAIZ / "dados/instancias.json"
    arquivo.parent.mkdir(exist_ok=True)
    arquivo.write_text(json.dumps(entradas,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Entradas exportadas: {arquivo}")


if __name__=="__main__":
    main()
