"""Testes de propriedades e oráculos independentes, não de aparência do código."""

import itertools
import random
import unittest
from math import isfinite

from projetos.comum import mapa, vizinhos
from projetos.p01_busca_informada import buscar as informada
from projetos.p02_busca_nao_informada import buscar as nao_informada, corredores, labirinto
from projetos.p03_busca_complexa import Acao, planejar, avaliar_politica
from projetos.p04_algoritmo_genetico import instancia as carga, exato, medidas, genetico, reparar
from projetos.p05_csp import Disciplina, instancia as cursos, resolver, validar, dominios, compativel
from projetos.p06_base_conhecimento import Regra, REGRAS, CONSULTAS, cenarios, frente, tras


def distancia_oraculo(grade, inicio, objetivo):
    """Relaxamento de Bellman-Ford sem heap ou heurística."""
    vertices = [(r, c) for r, linha in enumerate(grade) for c, v in enumerate(linha) if v]
    dist = {v: float("inf") for v in vertices}
    dist[inicio] = 0
    for _ in range(len(vertices)-1):
        mudou = False
        for v in vertices:
            for w in vizinhos(grade, v):
                novo = dist[v]+grade[w[0]][w[1]]
                if novo < dist[w]:
                    dist[w] = novo; mudou = True
        if not mudou:
            break
    return dist[objetivo]


class BuscaInformadaTest(unittest.TestCase):
    def test_otimalidade_e_caminhos_em_mapas_diferentes(self):
        for seed in range(12):
            grade = mapa(seed, 6, 8)
            alvo = (5, 7)
            otimo = distancia_oraculo(grade, (0, 0), alvo)
            for metodo in ("astar", "ucs", "gulosa"):
                with self.subTest(seed=seed, metodo=metodo):
                    r = informada(grade, (0, 0), alvo, metodo)
                    self.assertEqual(tuple(r["caminho"][0]), (0, 0))
                    self.assertEqual(tuple(r["caminho"][-1]), alvo)
                    self.assertTrue(all(b in list(vizinhos(grade, a)) for a,b in zip(r["caminho"], r["caminho"][1:])))
                    self.assertEqual(sum(grade[a][b] for a,b in r["caminho"][1:]), r["custo"])
                    self.assertGreaterEqual(r["custo"], otimo)
                    if metodo != "gulosa":
                        self.assertEqual(r["custo"], otimo)

    def test_objetivo_inicial(self):
        self.assertEqual(informada([[1]], (0,0), (0,0))["custo"], 0)

    def test_inacessivel(self):
        self.assertIsNone(informada([[1,0,1]], (0,0), (0,2))["custo"])


class BuscaNaoInformadaTest(unittest.TestCase):
    def test_otimalidade_bfs_iddfs_e_ordem_dfs(self):
        for n in (10, 20, 40, 80):
            grade, inicio, alvo = corredores(n)
            for metodo in ("bfs", "dfs", "iddfs"):
                r = nao_informada(grade, inicio, alvo, metodo)
                self.assertEqual(r["passos"], 2*n-2 if metodo == "dfs" else 4)

    def test_sem_solucao_e_objetivo_inicial(self):
        for metodo in ("bfs", "dfs", "iddfs"):
            self.assertIsNone(nao_informada([[1,0,1]], (0,0), (0,2), metodo)["passos"])
            self.assertEqual(nao_informada([[1]], (0,0), (0,0), metodo)["passos"], 0)

    def test_unitario_contra_oraculo(self):
        for seed in range(8):
            grade = mapa(seed, 4, 5, False)
            for metodo in ("bfs", "iddfs"):
                self.assertEqual(nao_informada(grade,(0,0),(3,4),metodo)["passos"],
                                 distancia_oraculo(grade,(0,0),(3,4)))

    def test_labirintos_sao_arvores_e_rotas_concordam(self):
        for seed in range(10):
            grade,inicio,alvo=labirinto(seed)
            vertices=[(r,c) for r,linha in enumerate(grade) for c,v in enumerate(linha) if v]
            self.assertEqual(sum(len(list(vizinhos(grade,s))) for s in vertices)//2,len(vertices)-1)
            dist=distancia_oraculo(grade,inicio,alvo)
            self.assertLess(dist,float("inf"))
            for metodo in ("bfs","dfs","iddfs"):
                self.assertEqual(nao_informada(grade,inicio,alvo,metodo)["passos"],dist)


class BuscaComplexaTest(unittest.TestCase):
    def test_garantia_exaustiva_e_valor_pior_caso(self):
        for bateria in range(16):
            r = planejar(bateria)
            trajetorias = avaliar_politica(r["politica"], ("Portaria", bateria))
            self.assertEqual(isfinite(r["valor"]), all(t[0] for t in trajetorias))
            if isfinite(r["valor"]):
                self.assertEqual(r["valor"], max(t[1] for t in trajetorias))
                self.assertTrue(all(e >= 0 for _,_,trilha in trajetorias for _,e in trilha))

    def test_contraexemplo_ao_otimismo(self):
        acoes = {"Portaria": (Acao("risco", 4, (("Laboratorio",1),("Desvio",1))),
                              Acao("segura", 8, (("Laboratorio",1),))), "Desvio": ()}
        self.assertEqual(planejar(2, True, acoes)["valor"], 8)
        self.assertEqual(planejar(2, False, acoes)["valor"], 4)

    def test_mais_bateria_nao_piora_valor(self):
        valores = [planejar(b)["valor"] for b in range(16)]
        self.assertTrue(all(a >= b for a,b in zip(valores,valores[1:])))


class GeneticoTest(unittest.TestCase):
    def test_programacao_dinamica_contra_forca_bruta(self):
        itens = carga()[:10]
        for limites in ((0,0), (12,10), (30,25), (65,48)):
            otimo = max(medidas(bits,itens)[2] for bits in itertools.product((0,1),repeat=10)
                        if all(x <= y for x,y in zip(medidas(bits,itens)[:2],limites)))
            valor,bits = exato(itens,limites)
            self.assertEqual(valor,otimo)
            self.assertEqual(medidas(bits,itens)[2],valor)
            self.assertTrue(all(x <= y for x,y in zip(medidas(bits,itens)[:2],limites)))

    def test_reparo_populacao_e_elitismo(self):
        itens, limites = carga(), (65,48)
        bits = reparar([1]*len(itens),itens,limites)
        self.assertTrue(all(x <= y for x,y in zip(medidas(bits,itens)[:2],limites)))
        r = genetico(itens,limites,42,populacao=20,geracoes=15)
        self.assertTrue(all(a <= b for a,b in zip(r["historico"],r["historico"][1:])))
        self.assertLessEqual(r["valor"],exato(itens,limites)[0])
        self.assertTrue(all(x <= y for x,y in zip(medidas(r["bits"],itens)[:2],limites)))

    def test_semente_reproduzivel(self):
        args = (carga(),(65,48),9)
        self.assertEqual(genetico(*args,populacao=12,geracoes=8),genetico(*args,populacao=12,geracoes=8))


class CSPTest(unittest.TestCase):
    def test_solucoes_validadas(self):
        for otimizado in (False,True):
            self.assertTrue(validar(cursos(),resolver(cursos(),otimizado)["solucao"]))

    def test_busca_contra_enumeracao(self):
        for n in (2,3):
            ds = [Disciplina(str(i),"P",(str(i),),32,True,(0,1)) for i in range(n)]
            dom = dominios(ds)
            existe = any(all(compativel(a,vs[i],b,vs[j]) for i,a in enumerate(ds)
                            for j,b in enumerate(ds) if i<j)
                         for vs in itertools.product(*(dom[d.nome] for d in ds)))
            for otimizado in (False,True):
                self.assertEqual(resolver(ds,otimizado)["solucao"] is not None,existe)

    def test_dominio_vazio(self):
        ds=[Disciplina("Impossivel","P",("A",),100,True)]
        for otimizado in (False,True):
            self.assertIsNone(resolver(ds,otimizado)["solucao"])


class ConhecimentoTest(unittest.TestCase):
    def test_concordancia_dos_motores(self):
        for nome,fatos in cenarios().items():
            fecho,provas,_=frente(fatos)
            for q in CONSULTAS:
                with self.subTest(cenario=nome,consulta=q):
                    self.assertEqual(q in fecho,tras(q,fatos)[0] is not None)
            self.assertEqual(set(provas),fecho)

    def test_provas_validas(self):
        indice={r.nome:r for r in REGRAS}
        def verificar(prova,fatos):
            if "fato" in prova:
                self.assertIn(prova["fato"],fatos)
                return prova["fato"]
            regra=indice[prova["regra"]]
            self.assertEqual(prova["conclusao"],regra.conclusao)
            self.assertEqual(tuple(verificar(p,fatos) for p in prova["premissas"]),regra.premissas)
            return regra.conclusao
        for fatos in cenarios().values():
            for prova in frente(fatos)[1].values():
                verificar(prova,fatos)

    def test_ciclos_regras_vazias_e_alternativas(self):
        regras=[Regra("a",("y",),"x"),Regra("b",("x",),"y"),Regra("c",("base",),"y")]
        self.assertEqual(frente(set(),regras)[0],set())
        self.assertIsNone(tras("x",set(),regras)[0])
        self.assertIsNotNone(tras("x",{"base"},regras)[0])
        self.assertIn("x",frente(set(),regras+[Regra("d",(),"base")])[0])

    def test_fecho_contra_oraculo_em_bases_aleatorias(self):
        rng=random.Random(31)
        atomos=list("abcdef")
        for _ in range(25):
            regras=[Regra(str(i),tuple(rng.sample(atomos,rng.randint(0,3))),rng.choice(atomos)) for i in range(12)]
            fatos=set(rng.sample(atomos,2)); fecho=set(fatos)
            while True:
                novo=fecho|{r.conclusao for r in regras if set(r.premissas)<=fecho}
                if novo==fecho:
                    break
                fecho=novo
            self.assertEqual(frente(fatos,regras)[0],fecho)
            for q in atomos:
                self.assertEqual(tras(q,fatos,regras)[0] is not None,q in fecho)

    def test_ausencia_nao_e_negacao(self):
        fecho,_,_=frente({"link_ativo"})
        self.assertNotIn("falha_dns",fecho)
        self.assertNotIn("rede_operacional",fecho)


if __name__ == "__main__":
    unittest.main()
