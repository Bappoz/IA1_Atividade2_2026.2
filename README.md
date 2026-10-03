# IA1 - Atividade 2: Métodos Clássicos de IA

**FGA0221 - Inteligência Artificial - T01 - UnB - 2026.2**

Lucas Andrade Zanetti - Matrícula **24/1039645**

Professor: Fabiano Araujo Soares

Seis projetos em Python com algoritmos implementados neste repositório, experimentos executados, figuras, testes de correção e relatório. Tema comum: decisões em um campus universitário. Todos os dados são **sintéticos**; não representam cadastros, medições ou instalações reais da UnB.

## Entrega e requisitos

- [Relatório PDF completo](output/pdf/relatorio_atividade2.pdf): **18 páginas, três por projeto**, incluindo figuras, tabelas, identificação e referências dentro de cada projeto. Não há capa externa.
- [Relatório em Markdown](relatorio/relatorio.md), gerado do mesmo conteúdo do PDF.
- [Texto editável](relatorio/conteudo.py): os números das tabelas vêm dos JSON dos experimentos.
- Pacote para entrega: `dist/IA1_Atividade2_241039645.zip`, criado por `python -m ferramentas.empacotar` (fora do Git).

| Requisito do item 9.2 | Implementação e problema | Comparação / verificação | Páginas |
| --- | --- | --- | --- |
| Busca informada | [p01_busca_informada.py](projetos/p01_busca_informada.py): A* para terreno com custos | UCS, gulosa e oráculo Bellman-Ford nos testes | 1-3 |
| Busca não informada | [p02_busca_nao_informada.py](projetos/p02_busca_nao_informada.py): corredores e labirintos | BFS, DFS e IDDFS | 4-6 |
| Busca complexa | [p03_busca_complexa.py](projetos/p03_busca_complexa.py): robô com bateria e ações não determinísticas | Política forte AND-OR versus planejamento otimista | 7-9 |
| Algoritmo genético | [p04_algoritmo_genetico.py](projetos/p04_algoritmo_genetico.py): mochila com massa e volume | Ótimo por programação dinâmica e ablação de mutação | 10-12 |
| CSP e métodos de solução | [p05_csp.py](projetos/p05_csp.py): disciplinas, salas e horários | Backtracking versus MRV, grau, LCV e MAC/AC-3 | 13-15 |
| Banco de conhecimentos | [p06_base_conhecimento.py](projetos/p06_base_conhecimento.py): triagem de rede | Horn, encadeamento para frente e para trás, árvores de prova | 16-18 |

Cada projeto explica o problema, descreve os algoritmos e a complexidade, apresenta imagens e valores medidos, documenta verificações e discute potenciais e limitações. O código contém comentários e docstrings em português. Bibliotecas externas fazem gráficos e PDF; os solucionadores são implementados em Python, sem pacotes de IA ou de otimização.

**“Busca complexa”** foi interpretada como busca em ambientes complexos com ações não determinísticas, usando árvores AND-OR. Essa classificação está na seção 4.3 do [sumário oficial de Russell e Norvig](https://aima.cs.berkeley.edu/contents). O projeto resolve um domínio acíclico de observação completa; não implementa planejamento com estados parcialmente observáveis ou políticas cíclicas.

## Executar

Ambiente verificado: Python 3.12.13. Instale as dependências em um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python executar.py
python -m unittest discover -s testes -v
python -m ferramentas.exportar_dados
python -m relatorio.gerar
python -m ferramentas.verificar_entrega
python -m ferramentas.empacotar
```

O repositório já contém resultados e PDF; é possível ler a entrega sem instalar nada. Os seis algoritmos e os testes usam somente a biblioteca padrão; executar os experimentos também requer Matplotlib, e gerar o relatório requer ReportLab e pypdf. O gerador usa fontes DejaVu quando disponíveis e fontes PDF padrão como alternativa.

Os módulos devem ser executados **da raiz do repositório**, conservando `projetos/comum.py` e `projetos/__init__.py`. Para repetir um projeto isolado:

```bash
python -m projetos.p01_busca_informada
python -m projetos.p02_busca_nao_informada
python -m projetos.p03_busca_complexa
python -m projetos.p04_algoritmo_genetico
python -m projetos.p05_csp
python -m projetos.p06_base_conhecimento
```

Após alterar código, dados ou parâmetros, execute novamente os experimentos afetados e regenere o relatório e o pacote. O gerador recusa overflow e verifica a paginação real do PDF. Em servidores sem diretório de configuração gravável para Matplotlib, use `MPLCONFIGDIR=/tmp/ia1-mpl python executar.py`.

## Experimentos e resultados

- P1: 30 mapas ponderados; os três métodos recebem o mesmo mapa. A* e UCS concordaram no ótimo em 30/30 mapas. A gulosa sacrifica qualidade de rota.
- P2: quatro tamanhos de corredor com duas rotas e dez labirintos com caminho único. A estrutura e a ordem dos vizinhos alteram o desempenho da DFS.
- P3: quatro capacidades de bateria; garantia verificada pela enumeração de todos os desfechos da política, sem simulação probabilística.
- P4: 30 sementes com mutação e 30 sem mutação, mesmos parâmetros restantes. O AG completo atingiu o ótimo de 374 em 29/30 execuções; não há garantia de ótimo por execução.
- P5: instância normal com 12 disciplinas e controle inviável com seis aulas do mesmo docente em cinco horários. A propagação reduziu tentativas, mas teve maior tempo medido nestas instâncias pequenas.
- P6: nove cenários e oito consultas; motores concordaram em 72/72 casos. Ausência de prova é desconhecimento, sem inferir negação.

Os JSON em `resultados/` guardam trajetórias, seleções, grades, regras e provas, não apenas números resumidos. `dados/instancias.json` reúne as entradas e sementes. `resultados/ambiente.json` registra versões e plataforma. Tempos são medições de uma execução, dependem da máquina e não sustentam inferência estatística. Contagem de fronteira/trilha não mede toda a RAM. O relatório explicita esses limites.

Verificação final: **21 testes aprovados**, incluindo comparações com oráculos independentes, casos sem solução, consistência de provas e reprodução por semente. O registro está em `resultados/testes.txt`. As 18 páginas foram renderizadas e inspecionadas visualmente; `resultados/revisao_final.md` registra a conferência.

## Estrutura

```text
projetos/        seis projetos e infraestrutura comum
testes/          testes com oráculos independentes e invariantes
dados/           entradas exportadas para inspeção
resultados/      JSON, figuras, registro de execução e auditoria
relatorio/       texto editável, Markdown e gerador de PDF
output/pdf/      PDF final, 18 páginas
ferramentas/     exportação, verificação e empacotamento
dist/           ZIP gerado para a entrega (fora do Git)
```

## Plano de ensino

Requisitos e prazo seguem o plano de ensino da disciplina: itens 9.2, 9.5 e 10. A entrega da atividade 2 está prevista para **09/10/2026**, pelo Teams, pasta **Avaliações / Atividade 2 / [matrícula]**.

Referência adicional para a lógica de cláusulas definidas: [Poole e Mackworth, seção 5.3](https://artint.info/3e/html/ArtInt3e.Ch5.S3.html). As fontes são conceituais; código e resultados não foram copiados de implementações externas.
