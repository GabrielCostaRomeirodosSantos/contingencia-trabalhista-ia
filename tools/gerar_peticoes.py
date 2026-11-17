# -*- coding: utf-8 -*-
"""Gera 3 petições iniciais FICTÍCIAS (PDF) para o modo demo."""
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

saida = sys.argv[1]

corpo = ParagraphStyle("corpo", fontName="Times-Roman", fontSize=11.5, leading=15,
                       alignment=TA_JUSTIFY, firstLineIndent=1.2 * cm, spaceAfter=6)
titulo = ParagraphStyle("titulo", fontName="Times-Bold", fontSize=12, leading=15,
                        alignment=TA_CENTER, spaceAfter=8)
secao = ParagraphStyle("secao", fontName="Times-Bold", fontSize=11.5, leading=15,
                       spaceBefore=8, spaceAfter=4)
aviso = ParagraphStyle("aviso", fontName="Times-Italic", fontSize=9, leading=11,
                       alignment=TA_CENTER, spaceAfter=10)
item = ParagraphStyle("item", parent=corpo, firstLineIndent=0, leftIndent=0.8 * cm, spaceAfter=3)

PETICOES = {
"peticao_01": {
 "sujeito": "A reclamante",
 "numero": "0000001-00.2026.5.06.0000 (FICTÍCIO)",
 "vara": "EXCELENTÍSSIMO(A) SENHOR(A) JUIZ(A) DA VARA DO TRABALHO DE RECIFE/PE",
 "partes": "MARIA DAS DORES SILVA SANTOS, auxiliar de serviços gerais, ajuíza reclamação trabalhista contra SUPERMERCADOS BOA COMPRA LTDA., pelos fatos e fundamentos a seguir.",
 "fatos": [
  "A reclamante foi admitida em 03/02/2021 como auxiliar de serviços gerais e dispensada sem justa causa em 15/05/2026, com aviso prévio indenizado. O último salário foi de R$ 1.850,00.",
  "A reclamada mantém mais de 200 empregados e uma loja com fluxo médio de 3.000 clientes por dia. Os banheiros da loja são de uso dos clientes e dos empregados. A reclamante limpava esses banheiros em média 12 vezes por dia, além de recolher o lixo de todos os sanitários, e recebia luvas e botas apenas de forma esporádica.",
  "A jornada ia das 06h às 15h40, de segunda-feira a sábado, com 30 minutos de intervalo para refeição. A reclamada não adota registro de ponto para os serviços gerais. Só os operadores de caixa marcam ponto.",
  "As verbas rescisórias foram pagas em 02/06/2026, depois do prazo de dez dias contados do término do contrato.",
  "Em diversas ocasiões o supervisor de loja chamou a reclamante de \"incompetente\" diante de clientes e de colegas, em tom de humilhação.",
 ],
 "pedidos": [
  ("a) Adicional de insalubridade em grau máximo (40%), pela limpeza e coleta de lixo de sanitários de grande circulação, com reflexos", "R$ 38.000,00"),
  ("b) Horas extras excedentes à oitava diária e à quadragésima quarta semanal, com adicional e reflexos", "R$ 42.000,00"),
  ("c) Intervalo intrajornada suprimido (30 minutos por dia), com reflexos", "R$ 21.000,00"),
  ("d) Multa do art. 477, § 8º, da CLT, pelo atraso no pagamento das verbas rescisórias", "R$ 1.850,00"),
  ("e) Indenização por dano moral, pelas humilhações reiteradas", "R$ 15.000,00"),
 ],
 "valor_causa": "R$ 117.850,00",
 "docs": "Documentos juntados: termo de rescisão, holerites dos últimos doze meses e extrato do FGTS.",
},
"peticao_02": {
 "sujeito": "O reclamante",
 "numero": "0000002-00.2026.5.06.0000 (FICTÍCIO)",
 "vara": "EXCELENTÍSSIMO(A) SENHOR(A) JUIZ(A) DA VARA DO TRABALHO DE JABOATÃO DOS GUARARAPES/PE",
 "partes": "CARLOS EDUARDO LIMA BARBOSA, motorista carreteiro, ajuíza reclamação trabalhista contra TRANSPORTADORA ROTA NORTE LTDA., pelos fatos e fundamentos a seguir.",
 "fatos": [
  "O reclamante foi admitido em 10/08/2019 como motorista carreteiro. O último salário foi de R$ 4.200,00. Em 02/04/2026 a reclamada o dispensou por justa causa, sob a acusação de desvio de carga.",
  "O reclamante nega o desvio. A carga foi roubada em rodovia federal durante uma viagem. Ele registrou boletim de ocorrência no mesmo dia, comunicou a empresa por mensagem e o rastreador do veículo mostra a parada forçada fora da rota. A reclamada registrou boletim próprio afirmando desvio, sem prova do alegado.",
  "O reclamante conduzia caminhão-tanque, com carga média de 30.000 litros de óleo diesel, por mais de dez viagens por mês.",
  "A reclamada controla a jornada por tacógrafo digital. O relatório do tacógrafo, anexo, mostra jornada média de 13h20 por dia, seis dias por semana, sem pagamento de horas extras.",
  "A reclamada divulgou a dispensa em grupo de aplicativo de mensagens dos motoristas e chamou o reclamante de \"ladrão de carga\". O grupo reúne mais de 80 pessoas.",
 ],
 "pedidos": [
  ("a) Reversão da justa causa e multa de 40% sobre o FGTS", "R$ 14.400,00"),
  ("b) Aviso prévio proporcional de 48 dias", "R$ 6.720,00"),
  ("c) Multa do art. 477, § 8º, da CLT", "R$ 4.200,00"),
  ("d) Horas extras, com adicional e reflexos, conforme relatório do tacógrafo", "R$ 68.000,00"),
  ("e) Adicional de periculosidade de 30%, pela condução de caminhão-tanque com inflamável, por cinco anos", "R$ 75.600,00"),
  ("f) Indenização por dano moral, pela acusação pública de furto", "R$ 30.000,00"),
 ],
 "valor_causa": "R$ 198.920,00",
 "docs": "Documentos juntados: boletim de ocorrência do reclamante, relatório do tacógrafo digital, mensagens com a reclamada e captura de tela do grupo de mensagens.",
},
"peticao_03": {
 "sujeito": "A reclamante",
 "numero": "0000003-00.2026.5.06.0000 (FICTÍCIO)",
 "vara": "EXCELENTÍSSIMO(A) SENHOR(A) JUIZ(A) DA VARA DO TRABALHO DE RECIFE/PE",
 "partes": "ANA PAULA FERREIRA CORDEIRO, analista de suporte, ajuíza reclamação trabalhista contra TECHSUL SOLUÇÕES DIGITAIS LTDA. (primeira reclamada) e BANCO HORIZONTE S.A. (segundo reclamado), pelos fatos e fundamentos a seguir.",
 "fatos": [
  "A reclamante foi contratada em 01/03/2022 pela primeira reclamada, mediante exigência de abertura de pessoa jurídica (MEI), para prestar serviços de suporte técnico exclusivamente ao segundo reclamado. A remuneração mensal era de R$ 6.500,00. O contrato terminou em 20/06/2026, sem aviso.",
  "A reclamante trabalhava na sede do banco, em estação fornecida por ele, das 08h às 18h30, com crachá de acesso, e atendia chamados de empregados do banco. Recebia ordens diretas de um gerente do banco, que aprovava férias e ausências, e cumpria metas fixadas pelo banco.",
  "Em momentos de pico, a reclamante respondia chamados à noite pelo aplicativo corporativo, o que consta nos registros de acesso do sistema do banco.",
  "Em reunião com mais de 20 pessoas, o gerente do banco criticou a reclamante de forma ríspida por não atingir meta. Ela não apresenta testemunhas nem gravação dessa reunião.",
  "Não houve pagamento de verbas rescisórias, de férias nem de décimo terceiro, e não houve depósitos de FGTS.",
 ],
 "pedidos": [
  ("a) Reconhecimento do vínculo de emprego, com anotação da CTPS, e pagamento de férias com 1/3, décimo terceiro e FGTS com multa de 40%, com responsabilidade subsidiária do segundo reclamado", "R$ 96.000,00"),
  ("b) Horas extras excedentes à jornada legal, com adicional e reflexos", "R$ 36.000,00"),
  ("c) Multa do art. 477, § 8º, da CLT", "R$ 6.500,00"),
  ("d) Indenização por dano moral decorrente de assédio moral", "R$ 25.000,00"),
 ],
 "valor_causa": "R$ 163.500,00",
 "docs": "Documentos juntados: contrato de prestação de serviços, notas fiscais mensais, crachá de acesso e registros de acesso ao sistema do banco.",
},
}

for chave, p in PETICOES.items():
    doc = SimpleDocTemplate(f"{saida}/{chave}.pdf", pagesize=A4,
                            leftMargin=2.5*cm, rightMargin=2.5*cm, topMargin=2.2*cm, bottomMargin=2.2*cm,
                            title=f"Petição inicial fictícia {chave}", author="Peça fictícia para demonstração")
    h = []
    h.append(Paragraph("PEÇA FICTÍCIA PARA DEMONSTRAÇÃO. Nomes, empresas e números de processo são inventados.", aviso))
    h.append(Paragraph(p["vara"], titulo))
    h.append(Paragraph(f"Processo nº {p['numero']}", aviso))
    h.append(Paragraph(p["partes"], corpo))
    h.append(Paragraph("DOS FATOS", secao))
    for f in p["fatos"]:
        h.append(Paragraph(f, corpo))
    h.append(Paragraph("DOS PEDIDOS", secao))
    h.append(Paragraph(f"{p['sujeito']} solicita a condenação da reclamada ao pagamento dos seguintes pedidos, com valores estimados nos termos do art. 840, § 1º, da CLT:", corpo))
    for d, v in p["pedidos"]:
        h.append(Paragraph(f"{d}: <b>{v}</b>.", item))
    h.append(Paragraph("DO VALOR DA CAUSA", secao))
    h.append(Paragraph(f"Atribui-se à causa o valor de <b>{p['valor_causa']}</b>.", corpo))
    h.append(Paragraph("DOS DOCUMENTOS", secao))
    h.append(Paragraph(p["docs"], corpo))
    h.append(Spacer(1, 6))
    h.append(Paragraph("Solicita-se, ainda, a concessão da justiça gratuita e a condenação da reclamada em honorários de sucumbência de 15%.", corpo))
    h.append(Paragraph("Termos em que pede deferimento.", corpo))
    doc.build(h)
    print("ok", chave)
