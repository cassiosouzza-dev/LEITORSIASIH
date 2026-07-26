"""Testes do motor de extração (prod_SIA_SIH2xlsx.py).

As funções puras (padronizar_*, limpar_valor) rodam sempre. Os testes de
integração usam os PDFs reais de exemplo que ficam na raiz do projeto mas
NÃO são versionados (dados reais de faturamento hospitalar) — por isso são
pulados automaticamente se os arquivos não existirem na máquina.
"""
import os

import pytest

from prod_SIA_SIH2xlsx import (
    detecting_tipo_relatorio,
    executar_extracao_completa,
    limpar_valor,
    padronizar_competencia,
    padronizar_nome_hospital,
    padronizar_subtipo,
    processar_ambulatorial,
    processar_hospitalar,
)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_AMBULATORIAL = os.path.join(RAIZ, "SANTA_CASA.pdf")
PDF_HOSPITALAR = os.path.join(RAIZ, "VALORES_BRUTOS_DE_PRODUCAO_202605_STA_CASA.pdf")

precisa_pdfs = pytest.mark.skipif(
    not (os.path.exists(PDF_AMBULATORIAL) and os.path.exists(PDF_HOSPITALAR)),
    reason="PDFs de exemplo não estão presentes nesta máquina (não são versionados)",
)


# --- Funções puras -----------------------------------------------------

def test_padronizar_subtipo_unifica_agora_tem_especialistas_truncado_e_completo():
    # Este era o bug original da sessão: SIA trunca o nome, SIH não, e viravam
    # subtipos "distintos" na tabela final por causa da grafia diferente.
    truncado = padronizar_subtipo("Programa Agora Tem Especialistas -Compon")
    completo = padronizar_subtipo("Programa Agora Tem Especialistas -Componente")
    assert truncado == completo == "Programa Agora Tem Especialistas -Componente"


def test_padronizar_subtipo_mantem_texto_desconhecido():
    assert padronizar_subtipo("Nefrologia") == "Nefrologia"


def test_padronizar_subtipo_texto_vazio():
    assert padronizar_subtipo("") == "não possui"


def test_padronizar_competencia_mes_por_extenso():
    assert padronizar_competencia("MAI/26") == "05/2026"


def test_padronizar_competencia_ja_padronizada():
    assert padronizar_competencia("05/2026") == "05/2026"


def test_padronizar_nome_hospital_reconhece_santa_casa():
    assert padronizar_nome_hospital("123 SANTA CASA DE MONTES CLAROS") == (
        "HOSPITAL SANTA CASA DE MONTES CLAROS"
    )


def test_limpar_valor_formato_brasileiro():
    assert limpar_valor("1.234,56") == 1234.56


def test_limpar_valor_invalido_retorna_zero():
    assert limpar_valor("abc") == 0.0


# --- Integração com PDFs reais -----------------------------------------

@precisa_pdfs
def test_detecta_tipo_ambulatorial():
    assert detecting_tipo_relatorio(PDF_AMBULATORIAL) == "AMBULATORIAL"


@precisa_pdfs
def test_detecta_tipo_hospitalar():
    assert detecting_tipo_relatorio(PDF_HOSPITALAR) == "HOSPITALAR"


@precisa_pdfs
def test_processar_ambulatorial_extrai_dados_consistentes():
    dados = processar_ambulatorial(PDF_AMBULATORIAL)
    assert len(dados) == 14
    hospitais = {d["Hospital/Prestador"] for d in dados}
    assert hospitais == {"HOSPITAL SANTA CASA DE MONTES CLAROS"}
    competencias = {d["Mês/Ano"] for d in dados}
    assert competencias == {"05/2026"}
    ambitos = {d["Âmbito Serviço"] for d in dados}
    assert ambitos == {"Ambulatorial"}
    total = sum(d["Valor"] for d in dados)
    assert total == pytest.approx(3749523.0, abs=0.01)


@precisa_pdfs
def test_processar_hospitalar_extrai_dados_consistentes():
    dados = processar_hospitalar(PDF_HOSPITALAR)
    assert len(dados) == 37
    hospitais = {d["Hospital/Prestador"] for d in dados}
    assert hospitais == {"HOSPITAL SANTA CASA DE MONTES CLAROS"}
    ambitos = {d["Âmbito Serviço"] for d in dados}
    assert ambitos == {"Hospitalar"}
    total = sum(d["Valor"] for d in dados)
    assert total == pytest.approx(4667224.61, abs=0.01)


@precisa_pdfs
def test_executar_extracao_completa_consolida_os_dois_arquivos():
    eventos = []
    df = executar_extracao_completa(
        [PDF_AMBULATORIAL, PDF_HOSPITALAR],
        callback_update=lambda msg, prog: eventos.append((msg, prog)),
    )
    assert len(df) == 14 + 37
    assert set(df["Âmbito Serviço"].unique()) == {"Ambulatorial", "Hospitalar"}
    assert list(df.columns) == [
        "Hospital/Prestador", "Mês/Ano", "Credor", "Âmbito Serviço",
        "Complexidade", "Financiamento", "Subtipo FAEC", "Valor",
    ]
    assert eventos  # callback foi chamado ao menos uma vez
