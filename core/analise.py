"""Análise ao vivo de uma petição inicial com a API gratuita do Google Gemini.

A chave de API é do autor do projeto e fica nos segredos do servidor (Streamlit Secrets ou variável
de ambiente). O avaliador não informa chave nenhuma. A chave nunca aparece na tela nem no código.
"""
import json
import re
import time

import requests

from pypdf import PdfReader

from .base import validar_analise

MODELO_PADRAO = "gemini-flash-latest"  # pode ser trocado em GEMINI_MODEL, sem mexer no código
MODELOS_RESERVA = ["gemini-flash-lite-latest"]  # usado se o principal continuar sobrecarregado
TENTATIVAS = 3
PAUSA_SEGUNDOS = 3
URL_API = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
MAX_PAGINAS = 25
MAX_CARACTERES = 60000


class ErroAnalise(Exception):
    """Erro com mensagem pronta para mostrar ao usuário."""


def extrair_texto(arquivo) -> str:
    """Extrai o texto de um PDF enviado. Limita páginas e tamanho para controlar custo."""
    try:
        leitor = PdfReader(arquivo)
    except Exception as erro:  # PDF corrompido ou protegido
        raise ErroAnalise(f"Não foi possível abrir o PDF: {erro}") from erro
    paginas = leitor.pages[:MAX_PAGINAS]
    texto = "\n".join((p.extract_text() or "") for p in paginas).strip()
    if len(texto) < 200:
        raise ErroAnalise(
            "O PDF não tem texto suficiente. Arquivos escaneados exigem OCR, que esta versão não faz."
        )
    return texto[:MAX_CARACTERES]


def _catalogo(base: dict) -> str:
    """Lista compacta dos fundamentos permitidos, para a IA citar só o que existe na base."""
    linhas = []
    for verba in base["verbas"]:
        linhas.append(f"VERBA {verba['id']}: {verba['verba']}")
        for f in verba["fundamentos"]:
            linhas.append(
                f"  - id={f['id']} | {f['tipo']} {f['numero']} | {f['titulo']} | {f['resumo']} | ALERTA: {f['alerta']}"
            )
    for f in base.get("pontos_gerais", []):
        linhas.append(
            f"PONTO GERAL id={f['id']} | {f['tipo']} {f['numero']} | {f['titulo']} | {f['resumo']}"
        )
    return "\n".join(linhas)


def montar_instrucoes(base: dict) -> str:
    criterio = base["criterio_risco"]
    return f"""Você é um advogado sênior de direito e processo do trabalho que analisa a contingência de uma reclamação trabalhista pelo lado da reclamada.
Leia a petição inicial e devolva APENAS um objeto JSON, sem texto antes ou depois.

REGRAS OBRIGATÓRIAS
1. Cite fundamentos jurídicos SOMENTE pelos ids do catálogo abaixo. Nunca invente súmula, OJ, tema ou número. Se nada do catálogo servir para um pedido, deixe "fundamentos" vazio.
2. Classifique cada pedido em um destes níveis, e apenas nestes: "provavel", "possivel", "remoto".
   - provavel: {criterio['provavel']}
   - possivel: {criterio['possivel']}
   - remoto: {criterio['remoto']}
3. Use o valor que a petição atribui a cada pedido. Se não houver valor, use 0 e diga isso na justificativa.
4. Quando o catálogo trouxer um ALERTA relevante ao caso (controvérsia, cancelamento, limite temporal), reflita-o na justificativa.
5. Não invente fatos que a petição não traz. Diga o que depende de prova ou perícia.
6. Escreva em português do Brasil, em frases diretas, sem gerúndios e sem latinismos.

FORMATO DO JSON
{{
  "titulo": "Autor x Réu (assunto)",
  "numero_processo": "número ou 'não informado'",
  "reclamante": "nome",
  "reclamada": "nome(s)",
  "vara": "vara ou 'não informada'",
  "contrato": {{"funcao": "", "admissao": "", "dispensa": "", "salario": 0, "modalidade": ""}},
  "valor_causa": 0,
  "resumo": "2 a 4 frases com o risco principal",
  "pedidos": [
    {{
      "id": "p1",
      "descricao": "texto curto do pedido",
      "valor": 0,
      "verba_id": "id da verba do catálogo ou null",
      "fundamentos": ["ids do catálogo"],
      "risco": "provavel | possivel | remoto",
      "justificativa": "por que esse nível, em 2 a 4 frases",
      "defesa": ["argumento ou providência de defesa"],
      "prova_chave": "prova que decide o pedido"
    }}
  ],
  "atencao_geral": ["ids de PONTO GERAL aplicáveis"],
  "proximos_passos": ["3 a 5 providências práticas"]
}}

CATÁLOGO DE FUNDAMENTOS PERMITIDOS
{_catalogo(base)}
"""


def _extrair_json(texto: str) -> dict:
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ErroAnalise("A IA não devolveu um JSON legível. Tente de novo.")
    bruto = texto[inicio : fim + 1]
    bruto = re.sub(r",\s*([}\]])", r"\1", bruto)  # remove vírgula sobrando
    try:
        return json.loads(bruto)
    except json.JSONDecodeError as erro:
        raise ErroAnalise(f"O JSON devolvido pela IA está inválido: {erro}") from erro


def _chamar(modelo: str, chave_api: str, corpo: dict):
    """Chama um modelo, com até 3 tentativas se o Google estiver sobrecarregado (500/503) ou a rede falhar."""
    resposta = None
    for tentativa in range(TENTATIVAS):
        try:
            resposta = requests.post(
                URL_API.format(modelo=modelo),
                headers={"x-goog-api-key": chave_api.strip(), "Content-Type": "application/json"},
                json=corpo,
                timeout=90,
            )
        except requests.RequestException:
            resposta = None
        if resposta is not None and resposta.status_code not in (500, 502, 503, 504):
            return resposta
        if tentativa < TENTATIVAS - 1:
            time.sleep(PAUSA_SEGUNDOS * (tentativa + 1))
    return resposta


def analisar_peticao(texto: str, chave_api: str, base: dict, modelo: str = MODELO_PADRAO):
    """Chama a API gratuita do Gemini e devolve (analise validada, avisos)."""
    if not chave_api or not chave_api.strip():
        raise ErroAnalise("A análise ao vivo não está configurada neste servidor.")
    corpo = {
        "systemInstruction": {"parts": [{"text": montar_instrucoes(base)}]},
        "contents": [{"role": "user", "parts": [{"text": f"PETIÇÃO INICIAL:\n\n{texto}"}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    modelos = [modelo] + [m for m in MODELOS_RESERVA if m != modelo]
    resposta = None
    for atual in modelos:
        resposta = _chamar(atual, chave_api, corpo)
        if resposta is not None and resposta.status_code < 500 and resposta.status_code != 404:
            break
        # 5xx ou rede: tenta o próximo modelo. 404 de modelo reserva também é ignorado.
        if resposta is not None and resposta.status_code == 404 and atual == modelo:
            break
    modelo = atual

    if resposta is None:
        raise ErroAnalise("Não foi possível falar com o serviço de IA. Tente de novo em instantes.")
    if resposta.status_code == 429:
        raise ErroAnalise("O limite gratuito da IA foi atingido. Espere alguns minutos e tente de novo.")
    if resposta.status_code in (400, 401, 403):
        try:
            detalhe = resposta.json().get("error", {}).get("message", "")
        except ValueError:
            detalhe = ""
        detalhe = (detalhe or "sem detalhe")[:300].replace(chave_api, "***")
        raise ErroAnalise(
            f"O serviço de IA recusou o pedido (código {resposta.status_code}). Motivo informado pelo Google: {detalhe}"
        )
    if resposta.status_code == 404:
        raise ErroAnalise("O modelo de IA configurado não existe mais. Avise o responsável pelo site.")
    if resposta.status_code >= 400:
        raise ErroAnalise(
            f"O serviço de IA está sobrecarregado (erro {resposta.status_code}). Espere um minuto e tente de novo."
        )

    try:
        dados = resposta.json()
        partes = dados["candidates"][0]["content"]["parts"]
        bruto_texto = "\n".join(p.get("text", "") for p in partes)
    except (ValueError, KeyError, IndexError, TypeError) as erro:
        raise ErroAnalise("A IA não devolveu uma resposta utilizável. Tente de novo.") from erro

    bruto = _extrair_json(bruto_texto)
    analise, avisos = validar_analise(bruto, base)
    analise["id"] = "ao_vivo"
    analise["revisao"] = {
        "gerada_por": f"Google Gemini ({modelo}), análise ao vivo",
        "status": "Análise automática, sem revisão humana",
    }
    return analise, avisos
