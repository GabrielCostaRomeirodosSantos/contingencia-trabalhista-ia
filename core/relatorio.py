"""Geração do relatório de contingência em .docx e do gráfico pizza."""
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt  # noqa: E402

from .base import (  # noqa: E402
    CORES,
    NOME_PRODUTO,
    RISCOS,
    ROTULOS,
    indice_fundamentos,
    moeda,
    rotulo_fundamento,
    totais_por_risco,
)

RECUO = Cm(3)


def grafico_png(totais: dict) -> bytes | None:
    """Pizza dos valores por nível de risco, com legenda grande e legível."""
    itens = [(r, totais[r]) for r in RISCOS if totais[r] > 0]
    if not itens:
        return None
    soma = sum(v for _, v in itens)
    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    ax.pie(
        [v for _, v in itens],
        colors=[CORES[r] for r, _ in itens],
        startangle=90,
        counterclock=False,
        wedgeprops={"edgecolor": "white", "linewidth": 2.5},
    )
    ax.set_aspect("equal")
    rotulos = [f"{ROTULOS[r]}: {moeda(v)} ({v / soma:.0%})" for r, v in itens]
    legenda = ax.legend(
        ax.patches,
        rotulos,
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        fontsize=15,
        frameon=False,
        handlelength=1.4,
        labelspacing=1.1,
    )
    for texto in legenda.get_texts():
        texto.set_color("#0b0b0b")
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buffer.getvalue()


def _formatar(par, negrito=False, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo=False, manter=True):
    fmt = par.paragraph_format
    fmt.space_before = Pt(0)
    fmt.space_after = Pt(0)
    fmt.line_spacing = 1.0
    fmt.keep_together = manter
    par.alignment = alinhamento
    if recuo:
        fmt.first_line_indent = RECUO
    for run in par.runs:
        run.font.name = "Calibri"
        run.font.size = Pt(12)
        run.italic = False
        if negrito:
            run.bold = True


def _par(doc, texto="", negrito=False, alinhamento=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo=False):
    par = doc.add_paragraph()
    if texto:
        par.add_run(texto)
    _formatar(par, negrito, alinhamento, recuo)
    return par


def _titulo(doc, texto):
    """Tópico em negrito e caixa alta, precedido de linha em branco, sempre junto ao texto seguinte."""
    _par(doc)
    par = _par(doc, texto.upper(), negrito=True, alinhamento=WD_ALIGN_PARAGRAPH.LEFT)
    par.paragraph_format.keep_with_next = True
    return par


def _rotulo_valor(doc, rotulo, valor):
    par = doc.add_paragraph()
    r1 = par.add_run(f"{rotulo}: ")
    par.add_run(valor)
    _formatar(par)
    r1.bold = True
    return par


def _sombrear(celula, cor_hex):
    tc_pr = celula._tc.get_or_add_tcPr()
    sombra = OxmlElement("w:shd")
    sombra.set(qn("w:val"), "clear")
    sombra.set(qn("w:color"), "auto")
    sombra.set(qn("w:fill"), cor_hex)
    tc_pr.append(sombra)


def _tabela(doc, cabecalho, linhas, larguras):
    tabela = doc.add_table(rows=1, cols=len(cabecalho))
    tabela.style = "Table Grid"
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, texto in enumerate(cabecalho):
        celula = tabela.rows[0].cells[i]
        celula.text = ""
        celula.paragraphs[0].add_run(texto)
        _formatar(celula.paragraphs[0], negrito=True)
        _sombrear(celula, "E7E6E1")
    for linha in linhas:
        celulas = tabela.add_row().cells
        for i, texto in enumerate(linha):
            celulas[i].text = ""
            celulas[i].paragraphs[0].add_run(str(texto))
            _formatar(celulas[i].paragraphs[0])
    for linha in tabela.rows:
        for i, largura in enumerate(larguras):
            linha.cells[i].width = Cm(largura)
        trpr = linha._tr.get_or_add_trPr()
        cant = OxmlElement("w:cantSplit")
        trpr.append(cant)
    return tabela


def gerar_docx(analise: dict, base: dict) -> bytes:
    indice = indice_fundamentos(base)
    totais = totais_por_risco(analise)
    contrato = analise.get("contrato", {})

    doc = Document()
    secao = doc.sections[0]
    secao.page_width, secao.page_height = Cm(21), Cm(29.7)
    secao.left_margin = secao.right_margin = Cm(2.5)
    secao.top_margin = secao.bottom_margin = Cm(2.5)
    estilo = doc.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(12)
    estilo.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")

    # Cabeçalho de três linhas centralizadas
    centro = WD_ALIGN_PARAGRAPH.CENTER
    _par(doc, NOME_PRODUTO.upper(), negrito=True, alinhamento=centro)
    _par(doc, "RELATÓRIO DE CONTINGÊNCIA TRABALHISTA", negrito=True, alinhamento=centro)
    _par(doc, f"PROCESSO Nº {analise.get('numero_processo', 'NÃO INFORMADO')}".upper(), negrito=True, alinhamento=centro)

    _titulo(doc, "1) Identificação")
    _rotulo_valor(doc, "Reclamante", analise.get("reclamante", "não informado"))
    _rotulo_valor(doc, "Reclamada", analise.get("reclamada", "não informada"))
    _rotulo_valor(doc, "Juízo", analise.get("vara", "não informado"))
    if contrato:
        _rotulo_valor(doc, "Função", contrato.get("funcao", ""))
        _rotulo_valor(doc, "Admissão", contrato.get("admissao", ""))
        _rotulo_valor(doc, "Término", contrato.get("dispensa", ""))
        if contrato.get("salario"):
            _rotulo_valor(doc, "Último salário", moeda(float(contrato["salario"])))
        _rotulo_valor(doc, "Modalidade", contrato.get("modalidade", ""))
    _rotulo_valor(doc, "Valor da causa", moeda(float(analise.get("valor_causa", 0))))

    _titulo(doc, "2) Resumo")
    _par(doc, analise.get("resumo", ""), recuo=True)

    _titulo(doc, "3) Quadro da contingência")
    soma = sum(totais.values()) or 1.0
    linhas = [
        (ROTULOS[r], moeda(totais[r]), f"{totais[r] / soma:.0%}") for r in RISCOS
    ] + [("Total", moeda(sum(totais.values())), "100%")]
    _tabela(doc, ["Nível de risco", "Valor atribuído", "Parcela"], linhas, [5.5, 6.0, 4.5])
    _par(doc)
    imagem = grafico_png(totais)
    if imagem:
        par = doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_before = Pt(0)
        par.paragraph_format.space_after = Pt(0)
        par.add_run().add_picture(io.BytesIO(imagem), width=Cm(15.5))
    _par(doc)
    _par(
        doc,
        "Os valores são os atribuídos pela parte autora na petição inicial, sem atualização monetária. "
        "A projeção do passivo exige cálculo próprio, com os índices vigentes.",
        recuo=True,
    )

    _titulo(doc, "4) Análise por pedido")
    for numero, pedido in enumerate(analise["pedidos"], start=1):
        par = _par(doc, "", alinhamento=WD_ALIGN_PARAGRAPH.LEFT)
        par.add_run(f"4.{numero}) {pedido['descricao']}").bold = True
        _formatar(par, alinhamento=WD_ALIGN_PARAGRAPH.LEFT)
        par.runs[0].bold = True
        par.paragraph_format.keep_with_next = True
        _rotulo_valor(doc, "Valor atribuído", moeda(pedido["valor"]))
        _rotulo_valor(doc, "Risco", ROTULOS[pedido["risco"]])
        _par(doc, pedido.get("justificativa", ""), recuo=True)
        if pedido["fundamentos"]:
            _rotulo_valor(doc, "Fundamentos", "")
            for fid in pedido["fundamentos"]:
                fund = indice[fid]
                _par(doc, f"- {rotulo_fundamento(fund)}: {fund['titulo']}.")
                if fund.get("alerta"):
                    _par(doc, f"  Alerta: {fund['alerta']}")
                for fonte in fund.get("fontes", [])[:2]:
                    _par(doc, f"  Fonte: {fonte}", alinhamento=WD_ALIGN_PARAGRAPH.LEFT)
        if pedido.get("defesa"):
            _rotulo_valor(doc, "Defesa", "")
            for item in pedido["defesa"]:
                _par(doc, f"- {item}")
        if pedido.get("prova_chave"):
            _rotulo_valor(doc, "Prova-chave", pedido["prova_chave"])
        _par(doc)

    if analise.get("atencao_geral"):
        _titulo(doc, "5) Pontos de atenção gerais")
        for fid in analise["atencao_geral"]:
            fund = indice[fid]
            _rotulo_valor(doc, rotulo_fundamento(fund), fund["titulo"])
            _par(doc, fund["resumo"], recuo=True)
            if fund.get("alerta"):
                _par(doc, f"Alerta: {fund['alerta']}", recuo=True)
            for fonte in fund.get("fontes", [])[:2]:
                _par(doc, f"Fonte: {fonte}", alinhamento=WD_ALIGN_PARAGRAPH.LEFT)
            _par(doc)

    if analise.get("proximos_passos"):
        _titulo(doc, "6) Próximos passos")
        for i, passo in enumerate(analise["proximos_passos"], start=1):
            par = doc.add_paragraph()
            par.add_run(f"{i}) ").bold = True
            par.add_run(passo)
            _formatar(par)
            par.runs[0].bold = True

    revisao = analise.get("revisao", {})
    _titulo(doc, "7) Origem e revisão")
    _rotulo_valor(doc, "Gerada por", revisao.get("gerada_por", "Claude (IA)"))
    _rotulo_valor(doc, "Situação", revisao.get("status", "Sem revisão"))

    saida = io.BytesIO()
    doc.save(saida)
    return saida.getvalue()
