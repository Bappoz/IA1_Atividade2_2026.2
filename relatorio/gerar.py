"""Gera PDF e Markdown a partir do mesmo conteúdo e dos resultados reais.

Execute da raiz: python -m relatorio.gerar
Não execute este arquivo diretamente: o módulo mantém importações reproduzíveis.
"""

import json
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, Preformatted
from pypdf import PdfReader
from .conteudo import construir, RAIZ


def fontes():
    """DejaVu é distribuída no Linux; fallback portátil é Helvetica/Courier."""
    base = Path("/usr/share/fonts/TTF")
    if not (base / "DejaVuSans.ttf").exists():
        base = Path("/usr/share/fonts/truetype/dejavu")
    if (base / "DejaVuSans.ttf").exists():
        for nome, arquivo in (("Texto","DejaVuSans.ttf"),("TextoNegrito","DejaVuSans-Bold.ttf"),
                              ("Codigo","DejaVuSansMono.ttf")):
            pdfmetrics.registerFont(TTFont(nome, str(base / arquivo)))
        return "Texto", "TextoNegrito", "Codigo"
    return "Helvetica", "Helvetica-Bold", "Courier"


def main():
    projetos = construir()
    saida = RAIZ / "output/pdf/relatorio_atividade2.pdf"
    saida.parent.mkdir(parents=True, exist_ok=True)
    regular, bold, mono = fontes()
    estilos = {
        "titulo": ParagraphStyle("Titulo", fontName=bold, fontSize=16, leading=21, textColor=colors.HexColor("#163548"), spaceAfter=9),
        "p": ParagraphStyle("Corpo", fontName=regular, fontSize=10, leading=14, alignment=TA_LEFT, spaceAfter=8),
        "h": ParagraphStyle("Secao", fontName=bold, fontSize=11, leading=15, spaceBefore=6, spaceAfter=6, textColor=colors.HexColor("#176b68")),
        "legenda": ParagraphStyle("Legenda", fontName=regular, fontSize=8.2, leading=11, spaceAfter=10, textColor=colors.HexColor("#4d6374")),
        "codigo": ParagraphStyle("Codigo", fontName=mono, fontSize=8.2, leading=11, spaceAfter=8, backColor=colors.HexColor("#f0f4f7"), borderPadding=6),
        "celula": ParagraphStyle("Celula", fontName=regular, fontSize=8.1, leading=10.6),
        "cabecalho": ParagraphStyle("Cabecalho", fontName=bold, fontSize=8.1, leading=10.6, textColor=colors.white),
    }
    W,H = A4
    largura = W-84
    doc = SimpleDocTemplate(str(saida), pagesize=A4, leftMargin=42, rightMargin=42,
                            topMargin=48, bottomMargin=42,
                            title="Atividade 2 - Métodos Clássicos de IA", author="Lucas Andrade Zanetti",
                            subject="Seis projetos Python - FGA0221 - 2026.2")
    elementos, markdown, alturas = [], [], []
    for proj in projetos:
        for i,pagina in enumerate(proj["paginas"],1):
            titulo = f"{proj['numero']:02d} | {proj['titulo']}"
            bloco = [Paragraph(escape(titulo), estilos["titulo"])]
            if i == 1:
                identidade = "Lucas Andrade Zanetti | Matrícula 24/1039645<br/>FGA0221 - T01 - Prof. Fabiano Araujo Soares | 30/09/2026"
                bloco.append(Paragraph(identidade, estilos["legenda"]))
                markdown.extend([f"# Projeto {proj['numero']} - {proj['titulo']}", "", "Lucas Andrade Zanetti - Matrícula 24/1039645", ""])
            markdown.extend([f"<!-- Página {i} de 3 deste projeto -->", ""])
            for item in pagina:
                tipo=item["tipo"]
                if tipo in {"p","h"}:
                    bloco.append(Paragraph(escape(item["texto"]), estilos[tipo]))
                    markdown.extend([("## " if tipo=="h" else "")+item["texto"], ""])
                elif tipo == "codigo":
                    bloco.append(Preformatted(item["texto"], estilos["codigo"]))
                    markdown.extend(["```text",item["texto"],"```",""])
                elif tipo == "tabela":
                    linhas=[[Paragraph(escape(str(c)),estilos["cabecalho"]) for c in item["cabecalho"]]]
                    linhas += [[Paragraph(escape(str(c)),estilos["celula"]) for c in linha] for linha in item["linhas"]]
                    n=len(item["cabecalho"])
                    # A primeira coluna contém nomes; recebe largura adicional.
                    widths=[largura*.25]+[largura*.75/(n-1)]*(n-1) if n>1 else [largura]
                    t=Table(linhas, colWidths=widths, repeatRows=1, hAlign="LEFT")
                    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1d4b60")),
                                           ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#eef4f7"),colors.white]),
                                           ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),6),
                                           ("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),
                                           ("BOTTOMPADDING",(0,0),(-1,-1),5),
                                           ("LINEBELOW",(0,-1),(-1,-1),.5,colors.HexColor("#cad7df"))]))
                    bloco.extend([t,Spacer(1,10)])
                    markdown.extend(["| "+" | ".join(item["cabecalho"])+" |","| "+" | ".join(["---"]*n)+" |"])
                    markdown.extend("| "+" | ".join(map(str,linha))+" |" for linha in item["linhas"])
                    markdown.append("")
                elif tipo == "figura":
                    arquivo=RAIZ / "resultados/figuras" / item["nome"]
                    img=Image(str(arquivo))
                    escala=min(largura/img.imageWidth,item["altura"]/img.imageHeight)
                    img.drawWidth=img.imageWidth*escala; img.drawHeight=img.imageHeight*escala
                    bloco.extend([img,Spacer(1,4),Paragraph(escape(item["legenda"]),estilos["legenda"])])
                    markdown.extend([f"![{item['legenda']}](../resultados/figuras/{item['nome']})",""])
            # Medida conservadora antes de compor: qualquer overflow é um erro.
            altura=0
            for e in bloco:
                _, alto=e.wrap(largura-12, H)
                altura += alto+e.getSpaceBefore()+e.getSpaceAfter()
            alturas.append({"projeto":proj["numero"],"pagina":i,"altura_pt":round(altura,1)})
            if altura > H-48-42-12:
                raise ValueError(f"Conteúdo não cabe: projeto {proj['numero']}, página {i}: {altura:.1f} pt")
            if elementos:
                elementos.append(PageBreak())
            elementos.extend(bloco)
    total = sum(len(p["paginas"]) for p in projetos)
    def moldura(canvas, documento):
        canvas.saveState()
        pagina=canvas.getPageNumber()
        projeto=(pagina-1)//3+1; interna=(pagina-1)%3+1
        canvas.setFont(regular,8)
        canvas.setFillColor(colors.HexColor("#547084"))
        canvas.drawString(42,H-25,"UNIVERSIDADE DE BRASÍLIA | ATIVIDADE 2 - MÉTODOS CLÁSSICOS DE IA")
        canvas.setStrokeColor(colors.HexColor("#c8d7df")); canvas.line(42,32,W-42,32)
        canvas.drawString(42,20,f"Projeto {projeto} | página {interna}/3 | dados sintéticos e algoritmos implementados no repositório")
        canvas.drawRightString(W-42,20,f"{pagina}/{total}")
        canvas.restoreState()
    doc.build(elementos,onFirstPage=moldura,onLaterPages=moldura)
    leitor=PdfReader(saida)
    if len(leitor.pages)!=total:
        raise RuntimeError(f"Paginação incorreta: {len(leitor.pages)}, esperado {total}")
    for j,pagina in enumerate(leitor.pages):
        esperado=f"{j//3+1:02d} |"
        if esperado not in pagina.extract_text():
            raise RuntimeError(f"Projeto incorreto na página {j+1}")
    (RAIZ / "relatorio/relatorio.md").write_text("\n".join(markdown),encoding="utf-8")
    auditoria={"paginas_totais":len(leitor.pages),"paginas_por_projeto":{str(p["numero"]):len(p["paginas"]) for p in projetos},
               "limite_por_projeto":4,"alturas_planejadas":alturas}
    (RAIZ / "resultados/auditoria_relatorio.json").write_text(json.dumps(auditoria,indent=2)+"\n")
    print(f"PDF criado: {saida} ({len(leitor.pages)} páginas; 3 por projeto)")


if __name__ == "__main__":
    main()
