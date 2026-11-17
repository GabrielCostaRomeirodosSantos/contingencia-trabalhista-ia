"""Carregamento da base jurídica e das análises de demonstração."""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

NOME_PRODUTO = "Contingência Trabalhista IA"  # nome provisório; troque aqui

RISCOS = ["provavel", "possivel", "remoto"]
ROTULOS = {"provavel": "Provável", "possivel": "Possível", "remoto": "Remoto"}
# Cores do conjunto de status (vermelho, âmbar, verde). A cor nunca vai sozinha:
# todo gráfico mostra o rótulo e o valor junto.
CORES = {"provavel": "#b8453f", "possivel": "#d9a23c", "remoto": "#4a9468"}
ICONES = {"provavel": "▲", "possivel": "◆", "remoto": "●"}


def moeda(valor: float) -> str:
    """Formata em reais no padrão brasileiro: R$ 1.234,56."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def carregar_base() -> dict:
    with open(RAIZ / "data" / "base_juridica.json", encoding="utf-8") as f:
        return json.load(f)


def indice_fundamentos(base: dict) -> dict:
    """Mapa id -> fundamento, incluindo os pontos gerais."""
    indice = {}
    for verba in base["verbas"]:
        for fund in verba["fundamentos"]:
            indice[fund["id"]] = fund
    for fund in base.get("pontos_gerais", []):
        indice[fund["id"]] = fund
    return indice


def ids_verbas(base: dict) -> list:
    return [v["id"] for v in base["verbas"]]


def rotulo_fundamento(fund: dict) -> str:
    """Rótulo curto, como 'Súmula TST 448'."""
    return f"{fund['tipo']} {fund['numero']}"


def carregar_demos() -> list:
    pasta = RAIZ / "data" / "demo"
    demos = []
    for caminho in sorted(pasta.glob("*.json")):
        with open(caminho, encoding="utf-8") as f:
            demos.append(json.load(f))
    return demos


def totais_por_risco(analise: dict) -> dict:
    totais = {r: 0.0 for r in RISCOS}
    for pedido in analise["pedidos"]:
        totais[pedido["risco"]] += float(pedido["valor"])
    return totais


def validar_analise(analise: dict, base: dict):
    """Garante que a análise só cita fundamentos da base e que os campos têm tipo certo.

    Retorna (analise limpa, lista de avisos). Fundamento fora da base é removido,
    para a IA nunca exibir uma súmula inventada.
    """
    avisos = []
    indice = indice_fundamentos(base)
    verbas = set(ids_verbas(base))
    pedidos_limpos = []
    for i, pedido in enumerate(analise.get("pedidos", []), start=1):
        risco = str(pedido.get("risco", "")).strip().lower()
        risco = risco.replace("á", "a").replace("í", "i").replace("é", "e")
        if risco not in RISCOS:
            avisos.append(f"Pedido {i}: risco '{pedido.get('risco')}' inválido; classificado como possível.")
            risco = "possivel"
        try:
            valor = float(pedido.get("valor", 0) or 0)
        except (TypeError, ValueError):
            avisos.append(f"Pedido {i}: valor ilegível; considerado R$ 0,00.")
            valor = 0.0
        fundamentos = []
        for fid in pedido.get("fundamentos", []) or []:
            if fid in indice:
                fundamentos.append(fid)
            else:
                avisos.append(f"Pedido {i}: o fundamento '{fid}' não consta da base e foi removido.")
        verba_id = pedido.get("verba_id")
        if verba_id not in verbas:
            verba_id = None
        pedidos_limpos.append({
            "id": pedido.get("id") or f"p{i}",
            "descricao": str(pedido.get("descricao", f"Pedido {i}")),
            "valor": valor,
            "verba_id": verba_id,
            "fundamentos": fundamentos,
            "risco": risco,
            "justificativa": str(pedido.get("justificativa", "")),
            "defesa": [str(d) for d in (pedido.get("defesa") or [])],
            "prova_chave": str(pedido.get("prova_chave", "")),
        })
    analise = dict(analise)
    analise["pedidos"] = pedidos_limpos
    analise["atencao_geral"] = [
        fid for fid in (analise.get("atencao_geral") or []) if fid in indice
    ]
    if not analise.get("valor_causa"):
        analise["valor_causa"] = sum(p["valor"] for p in pedidos_limpos)
    return analise, avisos
