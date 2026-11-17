"""Contingência Trabalhista IA: do PDF da petição ao mapa de risco."""
import hmac
import json
import os
import random
import re
from html import escape as esc

import plotly.graph_objects as go
import streamlit as st

from core import salvas
from core.contas import ErroConta, conferir, criar_conta
from core.analise import MODELO_PADRAO, ErroAnalise, analisar_peticao, extrair_texto
from core.base import (
    CORES,
    ICONES,
    NOME_PRODUTO,
    RAIZ,
    RISCOS,
    ROTULOS,
    carregar_base,
    carregar_demos,
    indice_fundamentos,
    moeda,
    rotulo_fundamento,
    totais_por_risco,
)
from core.relatorio import gerar_docx

MODO_DEMO = "Demonstração (sem custo)"
MODO_VIVO = "Análise ao vivo (IA gratuita)"
MODO_SALVAS = "Análises salvas"
LIMITE_ANALISES = 5
PIZZA_LARGURA = 230   # largura útil estimada da pizza (px)
PIZZA_ROTULO_ACIMA = 27  # espaço para o rótulo que sobe acima do círculo
ALTURA_FILTRO = 52  # altura reservada aos botões de filtro sob a pizza (px)

st.set_page_config(page_title=NOME_PRODUTO, page_icon="⚖️", layout="wide")

st.markdown(
    f"<style>{(RAIZ / 'assets' / 'estilo.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def _base():
    return carregar_base()


@st.cache_data(show_spinner=False)
def _demos():
    return carregar_demos()


@st.cache_data(show_spinner=False)
def _docx(analise_json: str, base_json: str) -> bytes:
    return gerar_docx(json.loads(analise_json), json.loads(base_json))


def segredo(nome: str) -> str:
    """Lê um segredo do Streamlit Secrets ou da variável de ambiente; devolve texto vazio se não existir."""
    try:
        valor = st.secrets.get(nome)
    except Exception:  # sem arquivo de segredos
        valor = None
    return str(valor or os.environ.get(nome, "")).strip()


def nome_arquivo(analise: dict) -> str:
    achado = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", analise.get("numero_processo", ""))
    numero = achado.group(0) if achado else "SEM NUMERO"
    return f"RELATORIO PROCESSO {numero}.docx"


def titulo_html(titulo: str) -> str:
    """Põe o trecho entre parênteses inteiro na linha de baixo."""
    if " (" in titulo and titulo.rstrip().endswith(")"):
        antes, resto = titulo.split(" (", 1)
        return f'{esc(antes)}<br><span class="complemento">({esc(resto)}</span>'
    return esc(titulo)


def ficha(analise: dict):
    numero = analise.get("numero_processo", "não informado").replace(" (FICTÍCIO)", "")
    campos = [
        ("Processo", numero, ""),
        ("Juízo", analise.get("vara", "não informado"), "ficticio"),
        ("Situação da análise", analise["revisao"]["status"], "ficticio"),
        ("Valor da causa", moeda(float(analise.get("valor_causa", 0))), ""),
    ]
    itens = "".join(
        f'<div><dt>{esc(rot)}</dt><dd class="{cls}">{esc(val)}</dd></div>' for rot, val, cls in campos
    )
    st.markdown(
        '<div class="cabeca">'
        f'<h1 class="caso">{titulo_html(analise.get("titulo", "Análise"))}</h1>'
        f'<dl class="dados">{itens}</dl>'
        "</div>",
        unsafe_allow_html=True,
    )


def altura_painel(analise: dict) -> int:
    """Altura (px) comum à pizza e à tabela, estimada pelo texto dos pedidos."""
    altura = 46 + 51  # cabeçalho e linha de total
    for pedido in analise["pedidos"]:
        linhas = -(-len(pedido["descricao"]) // 64)  # arredonda para cima
        altura += 51 + 21 * (max(linhas, 1) - 1)
    return max(altura, 330)


def _cor_filtrada(risco: str, filtro: list) -> str:
    """Cor da fatia: clareada quando há filtro ativo e o risco não está nele."""
    cor = CORES[risco]
    if filtro and risco not in filtro:
        r, g, b = (int(cor[i : i + 2], 16) for i in (1, 3, 5))
        return f"rgba({r},{g},{b},0.2)"
    return cor


def grafico_pizza(totais: dict, altura: int = 420, filtro: list | None = None):
    filtro = filtro or []
    itens = [(r, totais[r]) for r in RISCOS if totais[r] > 0]
    soma = sum(v for _, v in itens) or 1
    # ângulo do meio de cada fatia, a partir do topo, no sentido horário
    acumulado, acima = 0.0, False
    for _, v in itens:
        meio = (acumulado + v / 2) / soma * 360
        acumulado += v
        if min(meio, 360 - meio) < 32:
            acima = True
    topo = PIZZA_ROTULO_ACIMA if acima else 0
    area = altura - topo
    fig = go.Figure(
        go.Pie(
            domain={"x": [0.27, 0.73], "y": [max(0.3, 1 - PIZZA_LARGURA / area), 1]},
            labels=[ROTULOS[r] for r in RISCOS],  # os 3 riscos sempre na legenda
            values=[totais[r] for r in RISCOS],
            text=[
                (f"<b>{ROTULOS[r]} {f'{totais[r] / soma * 100:.1f}'.replace('.', ',')}%<br>{moeda(totais[r])}</b>" if r in filtro
                 else f"{ROTULOS[r]} {f'{totais[r] / soma * 100:.1f}'.replace('.', ',')}%<br>{moeda(totais[r])}")
                if totais[r] > 0 else ""
                for r in RISCOS
            ],
            textinfo="text",
            textposition="outside",
            automargin=False,
            textfont={"size": 16, "color": ["#A9B1BA" if filtro and r not in filtro else "#17212B" for r in RISCOS], "family": "Hanken Grotesk, Segoe UI, sans-serif"},
            marker={"colors": [_cor_filtrada(r, filtro) for r in RISCOS], "line": {"color": "white", "width": 3}},
            sort=False,
            pull=[0.07 if r in filtro else 0 for r in RISCOS],
            direction="clockwise",
            hovertemplate="%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        height=altura,
        margin={"l": 0, "r": 0, "t": topo, "b": 0},
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Hanken Grotesk, Segoe UI, sans-serif"},
    )
    return fig, soma


def mostrar_fundamento(fund: dict):
    alerta = f'<div class="alerta"><b>Atenção:</b> {esc(fund["alerta"])}</div>' if fund.get("alerta") else ""
    links = "".join(
        f'<a href="{esc(url)}" target="_blank" rel="noopener">Fonte {i}</a>'
        for i, url in enumerate(fund.get("fontes", []), start=1)
    )
    st.markdown(
        f'<div class="fund"><div class="nome">{esc(rotulo_fundamento(fund))}: {esc(fund["titulo"])}</div>'
        f'<p>{esc(fund["resumo"])}</p><div class="situacao">Situação: {esc(fund["status"])}</div>'
        f'{alerta}<div class="fontes">{links}</div></div>',
        unsafe_allow_html=True,
    )


def livro_de_pedidos(analise: dict, altura: int, filtro: list | None = None):
    filtro = filtro or []
    linhas = "".join(
        f'<tr class="{"destaque " + p["risco"] if p["risco"] in filtro else ""}"><td>{esc(p["descricao"])}</td>'
        f'<td class="risco"><span class="ico" style="color:{CORES[p["risco"]]}">{ICONES[p["risco"]]}</span>'
        f'{ROTULOS[p["risco"]]}</td><td class="num">{moeda(p["valor"])}</td></tr>'
        for p in analise["pedidos"]
    )
    total = sum(float(p["valor"]) for p in analise["pedidos"])
    st.markdown(
        f'<table class="livro" style="height:{altura}px"><thead><tr><th>Pedido</th><th>Risco</th><th class="num">Valor</th></tr></thead>'
        f'<tbody>{linhas}<tr class="total"><td>Total dos pedidos</td><td></td>'
        f'<td class="num">{moeda(total)}</td></tr></tbody></table>',
        unsafe_allow_html=True,
    )


def leitura(analise: dict):
    passos = ""
    if analise.get("proximos_passos"):
        itens = "".join(f"<li><b>{i})</b>{esc(p)}</li>" for i, p in enumerate(analise["proximos_passos"], start=1))
        passos = f"<h4>Próximos passos</h4><ol>{itens}</ol>"
    st.markdown(
        f'<div class="leitura"><h4>Resumo</h4><p>{esc(analise.get("resumo", ""))}</p>{passos}</div>',
        unsafe_allow_html=True,
    )


def tela_analise(analise: dict, base: dict, avisos: list):
    indice = indice_fundamentos(base)
    totais = totais_por_risco(analise)

    ficha(analise)
    for aviso in avisos:
        st.markdown(f'<div class="nota">{esc(aviso)}</div>', unsafe_allow_html=True)
    altura = altura_painel(analise)
    filtro: list = []
    coluna_pizza, coluna_tabela = st.columns([1, 1.5], gap="large")
    with coluna_pizza:
        if sum(totais.values()) > 0:
            with st.container(key="pizza"):
                area_grafico = st.container()
                filtro = st.pills(
                    "Filtrar por risco",
                    list(RISCOS),
                    format_func=lambda r: ROTULOS[r],
                    selection_mode="multi",
                    default=None,
                    key="filtro_risco",
                    label_visibility="collapsed",
                )
                with area_grafico:
                    fig, _ = grafico_pizza(totais, altura - ALTURA_FILTRO, filtro or [])
                    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        else:
            st.info("Nenhum valor atribuído aos pedidos.")
    with coluna_tabela:
        livro_de_pedidos(analise, altura, filtro if sum(totais.values()) > 0 else [])

    secao = st.segmented_control(
        "Seção",
        ["Início", "Resumo", "Pedidos", "Base jurídica"],
        selection_mode="single",
        default=None,
        key="secao",
        label_visibility="collapsed",
    )

    with st.container(key="folheio"):
        # a capa do livro aparece até a pessoa escolher uma aba; cada troca de aba vira páginas
        anterior = st.session_state.get("secao_anterior")
        if secao != anterior:
            st.session_state["secao_anterior"] = secao
            if secao in ABAS:
                destino = ABAS.index(secao)
                if anterior in ABAS:
                    passo = destino - ABAS.index(anterior)  # positivo: avança (esquerda); negativo: volta (direita)
                    paginas, sentido = abs(passo), ("esquerda" if passo > 0 else "direita")
                else:  # saindo da capa: abre o livro virando até a aba escolhida
                    paginas, sentido = destino + 1, "esquerda"
                st.session_state["viradas"] = st.session_state.get("viradas", 0) + 1
                st.markdown(folhas_html(paginas, st.session_state["viradas"], sentido), unsafe_allow_html=True)
        if secao is None:
            # a capa inteira é clicável: um botão invisível cobre o livro e abre a aba Início
            with st.container(key="capa_clicavel"):
                st.markdown(capa_html(), unsafe_allow_html=True)
                st.button("Abrir o livro na aba Início", key="abrir_livro", on_click=abrir_livro)
        if secao == "Início":
            esquerda, _ = st.columns([1.55, 1], gap="large")
            with esquerda:
                inicio()

        elif secao == "Resumo":
            esquerda, _ = st.columns([1.55, 1], gap="large")
            with esquerda:
                leitura(analise)

        elif secao == "Pedidos":
            for pedido in analise["pedidos"]:
                titulo = (
                    f"{ICONES[pedido['risco']]} {ROTULOS[pedido['risco']]}   {moeda(pedido['valor'])}   "
                    f"{pedido['descricao']}"
                )
                with st.expander(titulo):
                    st.markdown(f'<div class="leitura"><p>{esc(pedido["justificativa"])}</p></div>', unsafe_allow_html=True)
                    if pedido["fundamentos"]:
                        st.markdown("**Fundamentos**")
                        for fid in pedido["fundamentos"]:
                            mostrar_fundamento(indice[fid])
                    if pedido["defesa"]:
                        st.markdown("**Defesa**")
                        for item in pedido["defesa"]:
                            st.markdown(f"- {item}")
                    if pedido["prova_chave"]:
                        st.markdown(f"**Prova-chave:** {pedido['prova_chave']}")
            if analise.get("atencao_geral"):
                st.markdown("#### Pontos de atenção gerais")
                for fid in analise["atencao_geral"]:
                    mostrar_fundamento(indice[fid])

        elif secao == "Base jurídica":
            for verba in base["verbas"]:
                with st.expander(verba["verba"]):
                    for fund in verba["fundamentos"]:
                        mostrar_fundamento(fund)
            with st.expander("Pontos gerais: honorários e correção monetária"):
                for fund in base["pontos_gerais"]:
                    mostrar_fundamento(fund)


ABAS = ["Início", "Resumo", "Pedidos", "Base jurídica"]


def animacao_entrada(lado: str, usuario: str) -> str:
    """Refaz a tela de apresentação por cima do site: a balança pende, texto e barra somem, a balança cresce e a tela tomba."""
    sinal = "1" if lado == "direita" else "-1"
    origem = "100% 100%" if lado == "direita" else "0% 100%"
    nome = usuario if len(usuario) <= 18 else usuario[:17] + "…"
    tamanho = max(10, min(20, int(110 / (0.62 * max(len(nome), 1)))))
    cx = 340 if lado == "direita" else 60
    rotulo = (f'<text class="q-nome" x="{cx}" y="290" text-anchor="middle" font-size="{tamanho}">{esc(nome)}</text>')
    rot_esq = rotulo if lado == "esquerda" else ""
    rot_dir = rotulo if lado == "direita" else ""
    return f"""<div class="queda-tela" style="--s:{sinal};transform-origin:{origem}">
<div class="queda-lado"><div class="marca">{esc(NOME_PRODUTO)}</div>
<div class="queda-acesso"><b>Acesso</b><span>Conectado como {esc(usuario)}.</span></div></div>
<div class="queda-texto"><div class="leitura">{TEXTO_OBJETIVO}</div></div>
<svg class="queda-balanca" viewBox="0 0 400 360" preserveAspectRatio="xMidYMax meet" xmlns="http://www.w3.org/2000/svg" fill="none" stroke-linecap="round" stroke-linejoin="round">
<rect class="aco-p" x="190" y="104" width="20" height="214"/>
<rect class="aco-p" x="168" y="316" width="64" height="14" rx="2"/><rect class="aco-p" x="140" y="330" width="120" height="16" rx="3"/>
<rect class="aco-p" x="196" y="68" width="8" height="12"/><circle class="ou-p" cx="200" cy="56" r="14"/>
<g class="q-viga"><line class="aco" x1="48" y1="92" x2="352" y2="92" stroke-width="9"/>
<circle class="aco-p" cx="200" cy="92" r="13"/><circle class="ou" cx="200" cy="92" r="13" stroke-width="4"/></g>
<g class="q-prato q-esq"><g class="aco" stroke-width="3"><line x1="60" y1="92" x2="22" y2="228"/><line x1="60" y1="92" x2="98" y2="228"/></g>
<path class="aco-p" d="M10 228 Q60 296 110 228 Z"/><path class="ou" d="M10 228 L110 228" stroke-width="4"/>{rot_esq}</g>
<g class="q-prato q-dir"><g class="aco" stroke-width="3"><line x1="340" y1="92" x2="302" y2="228"/><line x1="340" y1="92" x2="378" y2="228"/></g>
<path class="aco-p" d="M290 228 Q340 296 390 228 Z"/><path class="ou" d="M290 228 L390 228" stroke-width="4"/>{rot_dir}</g>
</svg></div>"""


def abrir_livro():
    """Clique na capa: seleciona a aba Início (roda antes da página recarregar)."""
    st.session_state["secao"] = "Início"


def capa_html() -> str:
    """Capa de livro de direito (desenho próprio): couro bordô, moldura e balança dourada."""
    return """<div class="capa"><div class="capa-livro">
<div class="capa-moldura"></div>
<div class="capa-topo">DIREITO<br>DO TRABALHO</div>
<svg class="capa-balanca" viewBox="0 0 200 170" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="#d9b45f" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
<line x1="100" y1="18" x2="100" y2="146"/><circle cx="100" cy="14" r="5" fill="#d9b45f"/>
<line x1="34" y1="42" x2="166" y2="42"/>
<path d="M34 42 L14 98 M34 42 L54 98 M166 42 L146 98 M166 42 L186 98"/>
<path d="M10 98 H58 A24 16 0 0 1 10 98 Z" fill="#d9b45f" fill-opacity=".25"/>
<path d="M142 98 H190 A24 16 0 0 1 142 98 Z" fill="#d9b45f" fill-opacity=".25"/>
<path d="M70 146 H130 M80 156 H120"/></svg>
<div class="capa-sub">CLT &middot; Súmulas &middot; Jurisprudência</div>
<div class="capa-base">Contingência Trabalhista IA</div>
</div></div>"""


def folhas_html(quantidade: int, serie: int, sentido: str = "esquerda") -> str:
    """Páginas que se viram sobre o conteúdo: uma para Início, duas para Resumo, e assim por diante."""
    nome = f"virar{serie}"
    angulo = "-180deg" if sentido == "esquerda" else "180deg"
    folhas = "".join(
        f'<div class="folha {sentido}" style="z-index:{quantidade - i};animation-name:{nome};animation-delay:{i * 0.32:.2f}s"></div>'
        for i in range(quantidade)
    )
    return (
        f"<style>@keyframes {nome}{{0%{{transform:rotateY(0deg);opacity:1}}85%{{opacity:1}}"
        f"100%{{transform:rotateY({angulo});opacity:0}}}}</style><div class=\"folhas\">{folhas}</div>"
    )


def inicio():
    st.markdown(
        """<div class="leitura">
<h4>Função do site</h4>
<p>O site lê a petição inicial de uma reclamação trabalhista e estima a contingência de cada pedido. Também
classifica o risco em três categorias: provável, possível ou remoto. Cita o fundamento do TST e do STF, com o link
da fonte da informação, e soma o valor de cada faixa de risco. O resultado aparece no gráfico e na tabela acima, e
o relatório sai em Word.</p>
</div>""",
        unsafe_allow_html=True,
    )


TEXTO_OBJETIVO = """<h4>Objetivo do site</h4>
<p>O objetivo do site é dar rapidez e padrão à primeira triagem de uma reclamação trabalhista. Hoje, quem lê a
petição calcula o risco de cada pedido à mão, e a conclusão varia conforme o profissional que analisa.</p>
<p>Para isso, o site lê a petição inicial e separa os pedidos. Em seguida, classifica a chance de perda em provável,
possível ou remoto, com base em precedentes do TST e do STF, e soma quanto do valor da causa fica em cada categoria.
O resultado aparece em um gráfico, em uma tabela e em um relatório em Word.</p>
<p>A classificação busca evitar erros comuns, como uma súmula cancelada, uma regra alterada pela reforma
trabalhista ou um tema do STF ainda pendente. Toda citação traz o link da fonte e o alerta de controvérsia, para
conferência do advogado.</p>
<p>O site serve de apoio ao escritório e ao departamento jurídico. A análise ao vivo é automática, sem revisão
humana, e a decisão final cabe ao advogado responsável.</p>"""


def tela_sem_login():
    st.markdown(
        f'''<div class="leitura queda">
{TEXTO_OBJETIVO}
</div>
<div class="fundo-balanca"></div>''',
        unsafe_allow_html=True,
    )


def sobre():
    st.markdown(
        """<div class="prosa">
<h4>O problema</h4>
<p>Escritórios e departamentos jurídicos estimam a contingência de cada reclamação trabalhista à mão, e o
resultado varia conforme quem lê. O risco real fica nos detalhes: uma súmula cancelada, uma regra que mudou com a
reforma, um tema do STF pendente.</p>
<h4>O que o produto faz</h4>
<p>Lê a petição inicial, separa cada pedido, classifica o risco em provável, possível ou remoto e cita o
fundamento do TST ou do STF com o link da fonte. Mostra o valor de cada faixa e gera o relatório em Word.</p>
<h4>Como evita erro de IA</h4>
<p>A IA só cita fundamentos de uma base curada. Qualquer súmula fora da base é removida antes de aparecer na
tela. Cada item traz o alerta de controvérsia e o link para conferência.</p>
<h4>Limites</h4>
<p>O valor mostrado é o da petição, sem atualização monetária. A classificação é uma estimativa para apoiar a
decisão, e as análises de demonstração aguardam revisão do advogado responsável.</p>
</div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- barra lateral
base = _base()
demos = _demos()

with st.sidebar:
    st.markdown(f'<div class="marca">{esc(NOME_PRODUTO)}</div>', unsafe_allow_html=True)
    logado = bool(st.session_state.get("usuario"))
    analise, avisos = None, []
    if logado:
        st.subheader("Petição a analisar")
        modo = st.radio("Modo", [MODO_DEMO, MODO_VIVO, MODO_SALVAS], label_visibility="collapsed")

        if modo == MODO_DEMO:
            mapa = {d["titulo"]: d for d in demos}
            escolha = st.selectbox("Petição de demonstração", list(mapa))
            analise = mapa[escolha]
            pdf = RAIZ / analise["arquivo_pdf"]
            if pdf.exists():
                st.download_button(
                    "Baixar a petição (PDF)",
                    data=pdf.read_bytes(),
                    file_name=pdf.name,
                    mime="application/pdf",
                )
        elif modo == MODO_SALVAS:
            guardadas = salvas.listar(st.session_state["usuario"])
            if not guardadas:
                st.caption("Nenhuma análise salva ainda. Faça uma análise ao vivo e escolha Salvar.")
            else:
                rotulos = {f"{g['titulo']} ({g['criado_em'][8:10]}/{g['criado_em'][5:7]})": g["id"] for g in guardadas}
                escolhida = st.selectbox("Análise salva", list(rotulos))
                achada = salvas.carregar(st.session_state["usuario"], rotulos[escolhida])
                if achada:
                    analise, avisos = achada
                if st.button("Excluir esta análise", key="excluir_salva"):
                    salvas.excluir(st.session_state["usuario"], rotulos[escolhida])
                    st.rerun()
        else:
            st.caption(
                "Use só petições fictícias ou sem dados pessoais. O serviço gratuito de IA pode usar o texto "
                f"enviado para melhorar produtos do Google. Limite de {LIMITE_ANALISES} análises por sessão."
            )
            chave, modelo = segredo("GEMINI_API_KEY"), segredo("GEMINI_MODEL") or MODELO_PADRAO
            if not chave:
                st.warning("A análise ao vivo não está configurada neste servidor. Use o modo de demonstração.")
            ciclo = st.session_state.get("ciclo", 0)
            chaves_envio = [f"envio_{nome}_{ciclo}" for nome in ("lateral", "topo", "meio")]
            em_uso = next((c for c in chaves_envio if st.session_state.get(c) is not None), None)
            st.file_uploader(
                "PDF da petição inicial", type=["pdf"], key=chaves_envio[0],
                disabled=not logado or em_uso not in (None, chaves_envio[0]),
            )
            arquivo = st.session_state.get(em_uso) if em_uso else None
            usadas = st.session_state.get("usadas", 0)
            if st.button("Analisar petição", type="primary", disabled=not logado or usadas >= LIMITE_ANALISES or not chave):
                if arquivo is None:
                    st.error("Envie o PDF da petição.")
                else:
                    try:
                        with st.spinner("Lendo a petição e classificando os pedidos..."):
                            texto = extrair_texto(arquivo)
                            resultado, avisos_api = analisar_peticao(texto, chave, base, modelo)
                        st.session_state["ao_vivo"] = (resultado, avisos_api)
                        st.session_state["ao_vivo_decisao"] = None
                        st.session_state["usadas"] = usadas + 1
                        st.session_state["ciclo"] = ciclo + 1
                        st.rerun()
                    except ErroAnalise as erro:
                        st.error(str(erro))
            if usadas >= LIMITE_ANALISES:
                st.warning("Limite de análises da sessão atingido. Recarregue a página para recomeçar.")
            if "ao_vivo" in st.session_state:
                analise, avisos = st.session_state["ao_vivo"]
                decisao = st.session_state.get("ao_vivo_decisao")
                if decisao is None:
                    st.markdown("**Salvar esta análise?**")
                    col_sim, col_nao = st.columns(2)
                    if col_sim.button("Salvar", key="salvar_analise", width="stretch"):
                        salvas.salvar(st.session_state["usuario"], analise, avisos)
                        st.session_state["ao_vivo_decisao"] = "salva"
                        st.rerun()
                    if col_nao.button("Não salvar", key="nao_salvar_analise", width="stretch"):
                        st.session_state["ao_vivo_decisao"] = "descartada"
                        st.rerun()
                elif decisao == "salva":
                    st.caption("Análise salva. Ela aparece no modo Análises salvas.")

        if analise is not None:
            st.download_button(
                "Baixar relatório (.docx)",
                data=_docx(json.dumps(analise, ensure_ascii=False), json.dumps(base, ensure_ascii=False)),
                file_name=nome_arquivo(analise),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    with st.container(key="acesso"):
        st.subheader("Acesso")
        usuario_ok, senha_ok = segredo("APP_USUARIO"), segredo("APP_SENHA")
        if st.session_state.get("usuario"):
            st.caption(f"Conectado como {st.session_state['usuario']}.")
            if st.button("Sair", key="sair"):
                st.session_state.pop("usuario", None)
                st.session_state.pop("ao_vivo", None)
                st.session_state.pop("ao_vivo_decisao", None)
                st.rerun()
        else:
            acao = st.radio("Acesso", ["Entrar", "Criar conta"], horizontal=True, label_visibility="collapsed")
            tentativas = st.session_state.get("tentativas_login", 0)
            if acao == "Entrar":
                with st.form("login", border=False):
                    digitado_usuario = st.text_input("Usuário")
                    digitada_senha = st.text_input("Senha", type="password")
                    entrou = st.form_submit_button("Entrar")
                if entrou:
                    if tentativas >= 5:
                        st.error("Muitas tentativas. Recarregue a página para tentar de novo.")
                    else:
                        do_segredo = bool(usuario_ok and senha_ok) and hmac.compare_digest(
                            digitado_usuario.encode(), usuario_ok.encode()
                        ) and hmac.compare_digest(digitada_senha.encode(), senha_ok.encode())
                        if do_segredo or conferir(digitado_usuario, digitada_senha):
                            st.session_state["usuario"] = digitado_usuario.strip()
                            st.session_state["entrada_anim"] = random.choice(["esquerda", "direita"])
                            st.session_state["tentativas_login"] = 0
                            st.rerun()
                        else:
                            st.session_state["tentativas_login"] = tentativas + 1
                            st.error("Usuário ou senha incorretos.")
            else:
                with st.form("cadastro", border=False):
                    novo_usuario = st.text_input("Novo usuário")
                    nova_senha = st.text_input("Nova senha", type="password")
                    confirmacao = st.text_input("Repita a senha", type="password")
                    criou = st.form_submit_button("Criar conta")
                if criou:
                    try:
                        st.session_state["usuario"] = criar_conta(
                            novo_usuario, nova_senha, confirmacao, reservados=(usuario_ok,)
                        )
                        st.session_state["entrada_anim"] = random.choice(["esquerda", "direita"])
                        st.rerun()
                    except ErroConta as erro:
                        st.error(str(erro))

lado_entrada = st.session_state.pop("entrada_anim", None)
if lado_entrada:
    st.markdown(animacao_entrada(lado_entrada, st.session_state.get("usuario", "")), unsafe_allow_html=True)

if not logado:
    tela_sem_login()
elif analise is None and modo == MODO_SALVAS:
    st.info("Nenhuma análise salva. Faça uma análise ao vivo e escolha Salvar, na barra lateral.")
elif analise is None:
    st.info(
        "Envie o PDF de uma petição por qualquer um dos três campos de envio (botão, quadro ou barra lateral) "
        "e clique em Analisar petição, na barra lateral, para ver a análise."
        if logado
        else "Entre com usuário e senha, no campo Acesso da barra lateral, para usar a análise ao vivo."
    )
    with st.container(key="envio_topo"):
        st.file_uploader(
            "Enviar o PDF da petição", type=["pdf"], key=chaves_envio[1],
            label_visibility="collapsed", disabled=not logado or em_uso not in (None, chaves_envio[1]),
        )
    with st.container(key="envio_meio"):
        st.file_uploader(
            "PDF da petição inicial", type=["pdf"], key=chaves_envio[2],
            label_visibility="collapsed", disabled=not logado or em_uso not in (None, chaves_envio[2]),
        )
else:
    tela_analise(analise, base, avisos)
