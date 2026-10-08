"""Cria ZIP com PDF, fontes, relatório editável, dados, figuras e testes.

Não inclui Git, ambiente virtual, caches, páginas temporárias ou o próprio ZIP.
O manifesto SHA-256 permite conferir a integridade dos arquivos entregues.
"""
import hashlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from projetos.comum import RAIZ
from .verificar_entrega import main as verificar


def main():
    verificar()
    saida=RAIZ / "dist/IA1_Atividade2_241039645.zip"
    saida.parent.mkdir(exist_ok=True)
    ignorados={".git",".venv","venv",".vscode","__pycache__",".pytest_cache",".cache","tmp","dist"}
    arquivos=sorted(p for p in RAIZ.rglob("*") if p.is_file() and not ignorados.intersection(p.relative_to(RAIZ).parts))
    manifesto=[]
    prefixo="IA1_Atividade2_241039645"
    with ZipFile(saida,"w",compression=ZIP_DEFLATED,compresslevel=9) as z:
        for p in arquivos:
            rel=p.relative_to(RAIZ).as_posix()
            z.write(p,f"{prefixo}/{rel}")
            manifesto.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel}")
        z.writestr(f"{prefixo}/MANIFESTO_SHA256.txt","\n".join(manifesto)+"\n")
    with ZipFile(saida) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP corrompido")
    print(f"Pacote criado: {saida} ({len(arquivos)} arquivos e manifesto)")


if __name__=="__main__":
    main()
