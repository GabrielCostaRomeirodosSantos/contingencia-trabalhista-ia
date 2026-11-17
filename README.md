# Contingência Trabalhista IA

Lê a petição inicial de uma reclamação trabalhista, classifica o risco de cada pedido
(provável, possível ou remoto) e cita o fundamento do TST ou do STF, com link da fonte.
Mostra o valor por faixa de risco e gera o relatório em Word.

Projeto do Desafio de Inovação do processo seletivo do CITi.

## Como rodar no seu computador

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Dois modos

- **Demonstração:** 3 petições fictícias com análise já gerada. Não chama API e não tem custo.
- **Análise ao vivo:** o usuário envia um PDF e a IA gratuita do Google Gemini faz a análise. O avaliador
  não informa chave: a chave do autor fica nos segredos do servidor (`GEMINI_API_KEY`, no Streamlit Secrets
  ou em `.streamlit/secrets.toml`, que não vai para o GitHub). O modelo padrão é `gemini-flash-latest`
  e pode ser trocado em `GEMINI_MODEL`. A camada gratuita tem limite de uso e pode usar o texto enviado
  para melhorar produtos do Google: use só petições fictícias ou sem dados pessoais.

## Estrutura

- `app.py`: telas do Streamlit.
- `core/base.py`: leitura da base jurídica e validação da análise.
- `core/analise.py`: leitura do PDF e chamada à API do Gemini.
- `core/relatorio.py`: gráfico e relatório em Word.
- `data/base_juridica.json`: fundamentos curados, com status, alertas e links.
- `data/demo/`: análises de demonstração.
- `data/peticoes/`: petições fictícias em PDF.
- `tools/gerar_peticoes.py`: script que gerou as petições fictícias.

## Como a IA é impedida de inventar súmula

A IA só pode citar fundamentos pelos ids da base. Antes de mostrar o resultado, o app remove
qualquer fundamento fora da base. Cada item da base traz alerta de controvérsia e links para conferência.

## Limites

O valor mostrado é o atribuído pela petição, sem atualização monetária. PDFs escaneados exigem OCR,
que esta versão não faz. As análises de demonstração foram revisadas pelo autor com a ajuda da IA.
