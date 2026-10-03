"""Executa os seis experimentos e registra o ambiente de reprodução."""
import importlib
import platform
import sys
from datetime import datetime, timezone
from projetos.comum import salvar

MODULOS = ["p01_busca_informada", "p02_busca_nao_informada", "p03_busca_complexa",
           "p04_algoritmo_genetico", "p05_csp", "p06_base_conhecimento"]


def main():
    for nome in MODULOS:
        print(f"Executando {nome}...", flush=True)
        importlib.import_module(f"projetos.{nome}").executar()
    import matplotlib
    salvar("ambiente", {"python": sys.version, "plataforma": platform.platform(),
                        "matplotlib": matplotlib.__version__,
                        "data_utc": datetime.now(timezone.utc).isoformat(),
                        "observacao": "Tempos são medições de uma execução e dependem da máquina."})
    print("Resultados e figuras atualizados.")


if __name__ == "__main__":
    main()
