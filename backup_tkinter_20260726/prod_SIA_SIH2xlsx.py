import pdfplumber
import pandas as pd
import re
import os
import unicodedata

# ==============================================================================
# 1. CONFIGURAÇÕES E MAPAS
# ==============================================================================
MAPA_HOSPITAIS = {
    "SANTA CASA": "HOSPITAL SANTA CASA DE MONTES CLAROS",
    "MARIO RIBEIRO": "HOSPITAL DAS CLINICAS DOUTOR MARIO RIBEIRO DA SILVEIRA",
    "DAS CLINICAS": "HOSPITAL DAS CLINICAS DOUTOR MARIO RIBEIRO DA SILVEIRA",
    "DILSON GODINHO": "HOSPITAL DILSON GODINHO",
    "AROLDO TOURINHO": "HOSPITAL AROLDO TOURINHO",
    "CLEMENTE DE FARIA": "HOSPITAL UNIVERSITARIO CLEMENTE DE FARIA",
    "UNIVERSITARIO": "HOSPITAL UNIVERSITARIO CLEMENTE DE FARIA"
}

MAPA_MESES = {
    "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04", "MAI": "05", "JUN": "06",
    "JUL": "07", "AGO": "08", "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12"
}

# LINHAS IGNORADAS
LINHAS_IGNORADAS = [
    "SIA/SUS", "SIH/SUS", "MS/DATASUS", "SISTEMA DE INFORMACOES",
    "VALORES APROVADOS", "PAGINA:", "VERSAO", "EMISSAO", "COMPETENCIA",
    "TOTAL GERAL", "TOTAL DO", "A TRANSFERIR", "RETENCAO",
    "CONTRATUALIZACAO", "INCREMENTO", "CNES", "MUNICIPIO", "GESTOR",
    "CPF/CNS", "CNPJ", "SUB. TIPO FINANC", "FINANC.", "SEM CONTRATO", "COM CONTRATO",
    "SAS/DATASUS", "SECRETARIA MUNICIPAL", "CPF", "CNS"
]


# ==============================================================================
# 2. FUNÇÕES AUXILIARES
# ==============================================================================
def normalizar_texto(texto):
    if not texto: return ""
    nfkd = unicodedata.normalize('NFKD', texto)
    return u"".join([c for c in nfkd if not unicodedata.combining(c)]).lower()


def padronizar_competencia(texto_data):
    if not texto_data or texto_data == "DESCONHECIDA": return texto_data
    texto_data = texto_data.upper().strip()
    if re.match(r'^\d{2}/\d{4}$', texto_data): return texto_data
    partes = texto_data.split('/')
    if len(partes) == 2:
        mes, ano = partes[0].strip(), partes[1].strip()
        mes_final = mes.zfill(2) if mes.isdigit() else MAPA_MESES.get(mes, "00")
        ano_final = "20" + ano if len(ano) == 2 else ano
        if mes_final != "00": return f"{mes_final}/{ano_final}"
    return texto_data


def padronizar_nome_hospital(texto_cru):
    if not texto_cru: return "DESCONHECIDO"
    texto_upper = texto_cru.upper()
    for chave, nome_oficial in MAPA_HOSPITAIS.items():
        if chave in texto_upper: return nome_oficial
    return re.sub(r'^[\d\s\-\.]+', '', texto_cru).strip()


def padronizar_complexidade(texto):
    t = texto.strip().upper()
    if "MEDIA" in t: return "MEDIA COMPLEXIDADE"
    if "ALTA" in t: return "ALTA COMPLEXIDADE"
    if "ATENCAO BASICA" in t: return "ATENCAO BASICA"
    if "NAO SE APLICA" in t: return "NAO SE APLICA"
    return t


def padronizar_subtipo(texto):
    if not texto or texto == "não possui": return "não possui"
    texto = texto.strip()
    if texto.endswith('.'): texto = texto[:-1]

    texto_upper = normalizar_texto(texto).upper()

    if "DIAGNOSTICO" in texto_upper and "ONCOLOGIA" in texto_upper:
        return "Diagnóstico/tratamento em oncologia"

    if texto_upper.startswith("REDUCAO DAS FILAS"): return "Redução das Filas de Procedimentos Eletivos"
    if texto_upper.startswith("TRANSPLANTE"): return "Transplantes de orgãos, tecidos e células"
    if texto_upper.startswith(
            "CIRURGIA DO APARELHO DIGESTIVO"): return "Cirurgia do aparelho digestivo, orgãos anexos e parede abdominal"
    if texto_upper.startswith("ALTA COMPLEXIDADE EM CARDIOLOGIA"): return "Alta Complexidade em Cardiologia"
    if texto_upper.startswith("PROGRAMA AGORA TEM ESPECIALISTAS"): return "Programa Agora Tem Especialistas -Componente"
    if "DOENCA MACULAR" in texto_upper: return "Tratamento de Doença Macular"

    if "TROMBOFILIA" in texto_upper: return "Diagnóstico de trombofilia em gestante"
    # --------------------------------

    return texto


def limpar_valor(valor_str):
    if not valor_str: return 0.0
    limpo = valor_str.replace('.', '').replace(',', '.')
    try:
        return float(limpo)
    except ValueError:
        return 0.0


def extrair_metadados_generico(texto_completo):
    competencia = "DESCONHECIDA"
    texto_norm = normalizar_texto(texto_completo)
    match_comp = re.search(r'competencia\s*[:\s]\s*([\w/]+)', texto_norm)
    if match_comp:
        match_orig = re.search(r'(?i)compet[eê]ncia\s*[:\s]\s*([\w/0-9]+)', texto_completo)
        if match_orig: competencia = match_orig.group(1).upper()
    return competencia


def detecting_tipo_relatorio(caminho_pdf):
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            if not pdf.pages: return "DESCONHECIDO"
            primeira_pag = pdf.pages[0].extract_text()
            if not primeira_pag: return "DESCONHECIDO"
            texto_norm = normalizar_texto(primeira_pag).upper()
            if "SIHD2" in texto_norm or "SISTEMA DE INFORMACOES HOSPITALARES" in texto_norm: return "HOSPITALAR"
            if "SIA/SUS" in texto_norm or "SISTEMA DE INFORMACOES AMBULATORIAIS" in texto_norm: return "AMBULATORIAL"
            return "DESCONHECIDO"
    except:
        return "ERRO"


# ==============================================================================
# 3. AGRUPAMENTO DE LINHAS (Tolerância 6)
# ==============================================================================
def agrupar_palavras_em_linhas(words, tolerance=6):
    if not words: return []
    sorted_words = sorted(words, key=lambda w: w['top'])
    lines = []
    current_line = [sorted_words[0]]
    current_y = sorted_words[0]['top']
    for w in sorted_words[1:]:
        if abs(w['top'] - current_y) <= tolerance:
            current_line.append(w)
        else:
            lines.append(current_line)
            current_line = [w]
            current_y = w['top']
    lines.append(current_line)
    return lines


# ==============================================================================
# 4. PROCESSADORES
# ==============================================================================
def processar_hospitalar(caminho_pdf):
    dados = []
    with pdfplumber.open(caminho_pdf) as pdf:
        texto_completo = ""
        for page in pdf.pages: texto_completo += page.extract_text() + "\n"
        competencia = padronizar_competencia(extrair_metadados_generico(texto_completo))
        hospital_principal = "DESCONHECIDO"
        linhas = texto_completo.split('\n')

        # Busca do hospital principal
        for linha in linhas:
            linha_norm = normalizar_texto(linha)
            if ("executor" in linha_norm or "estabelecimento" in linha_norm) and "hospital" in linha_norm:
                match_nome = re.search(r'(?:EXECUTOR|ESTABELECIMENTO).*?[:\-]\s*(.*)', linha, re.IGNORECASE)
                if match_nome:
                    hospital_principal = padronizar_nome_hospital(match_nome.group(1))
                    break

        executor_atual = "Hospital"

        for page in pdf.pages:
            lines = page.extract_text().split('\n')
            for line in lines:
                line_norm = normalizar_texto(line)

                # Detecção de mudança de executor (acontece antes do filtro para não perder o estado)
                if "executor" in line_norm:
                    if "coopanest" in line_norm:
                        executor_atual = "COOPANEST"
                    elif "sancoop" in line_norm:
                        executor_atual = "SANCOOP"
                    else:
                        executor_atual = "Hospital"

                # 1. Filtro Geral (palavras ignoradas)
                if any(t in line_norm.upper() for t in LINHAS_IGNORADAS): continue

                # 2. OTIMIZAÇÃO: Filtro Estrito Antecipado
                # Se a linha não tiver uma barra '/', ela com certeza não é um procedimento válido.
                # Isso evita rodar o REGEX pesado abaixo desnecessariamente.
                if "/" not in line: continue

                # 3. Extração via Regex (só roda se passou pelos filtros acima)
                match_linha = re.search(r'^(.*?)\s+([\d\.]+,\d{2})\s+([\d\.]+,\d{2})$', line)
                if match_linha:
                    descricao = match_linha.group(1).strip()
                    val_sem = limpar_valor(match_linha.group(2))
                    val_com = limpar_valor(match_linha.group(3))
                    total = val_sem + val_com

                    if total == 0: continue
                    # (A verificação da barra '/' aqui se tornou redundante, mas mal não faz manter)
                    if "/" not in descricao: continue

                    complexidade = ""
                    financiamento = ""
                    subtipo = "não possui"

                    partes = descricao.split('/', 1)
                    if len(partes) > 0: complexidade = padronizar_complexidade(partes[0].strip())
                    if any(t in complexidade for t in LINHAS_IGNORADAS): continue

                    if len(partes) > 1:
                        resto = partes[1].strip()
                        if " - " in resto:
                            f, s = resto.split(" - ", 1)
                            financiamento = f.strip()
                            subtipo = s.strip()
                        else:
                            financiamento = resto

                        # ===> LINHA NOVA: Remove os parênteses na força bruta <===
                    financiamento = financiamento.replace("(MAC)", "MAC")

                    if "MAC" in financiamento.upper() or "MEDIA E ALTA" in normalizar_texto(financiamento).upper():
                        financiamento = "MAC"

                    if financiamento == "MAC":
                        subtipo = "BLMAC"
                    else:
                        subtipo = padronizar_subtipo(subtipo)

                    dados.append({
                        "Hospital/Prestador": hospital_principal,
                        "Mês/Ano": competencia,
                        "Credor": executor_atual,
                        "Âmbito Serviço": "Hospitalar",
                        "Complexidade": complexidade,
                        "Financiamento": financiamento,
                        "Subtipo FAEC": subtipo,
                        "Valor": total
                    })
    return dados


def processar_ambulatorial(caminho_pdf):
    dados = []
    with pdfplumber.open(caminho_pdf) as pdf:
        texto_paginas = ""
        for page in pdf.pages: texto_paginas += page.extract_text() + "\n"
        competencia = padronizar_competencia(extrair_metadados_generico(texto_paginas))
        hospital_oficial = "DESCONHECIDO"
        linhas_texto = texto_paginas.split('\n')
        for line in linhas_texto[:40]:
            if "CNES" in line:
                match = re.search(r'CNES\s*[:]\s*\d+\s+(.*)', line)
                if match:
                    hospital_oficial = padronizar_nome_hospital(match.group(1))
                    break

        curr_complexidade = ""
        curr_financiamento = ""
        textos_pendentes = []
        flag_cabecalho_recente = False

        for page in pdf.pages:
            words = page.extract_words(x_tolerance=3, keep_blank_chars=True)
            linhas_agrupadas = agrupar_palavras_em_linhas(words, tolerance=6)

            # --- CORREÇÃO DE MARGEM DINÂMICA ---
            # 1. Coleta todas as posições X iniciais das linhas válidas desta página
            x_iniciais_validos = []
            for palavras_linha in linhas_agrupadas:
                palavras_linha.sort(key=lambda w: w['x0'])
                texto_linha_raw = " ".join([w['text'] for w in palavras_linha])
                # Ignora linhas de cabeçalho padrão para não sujar o cálculo da margem
                if not any(ign in normalizar_texto(texto_linha_raw).upper() for ign in LINHAS_IGNORADAS):
                    x_iniciais_validos.append(palavras_linha[0]['x0'])
            
            # 2. Define a margem mínima (onde o texto começa)
            margem_dinamica = min(x_iniciais_validos) if x_iniciais_validos else 0
            
            # 3. Define o limite com uma tolerância pequena (ex: 10 pontos além da margem)
            LIMITE_NIVEL_1 = margem_dinamica + 10 
            # -----------------------------------

            for palavras_linha in linhas_agrupadas:
                palavras_linha.sort(key=lambda w: w['x0'])
                texto_linha = " ".join([w['text'] for w in palavras_linha])
                x_inicio = palavras_linha[0]['x0']
                line_clean = texto_linha.strip()
                line_norm = normalizar_texto(line_clean)

                if any(t in line_clean.upper() for t in LINHAS_IGNORADAS): continue

                match_valor = re.search(r'([\d\.]+,\d{2})$', line_clean)
                tem_valor = bool(match_valor)
                valor = 0.0
                texto_conteudo = line_clean

                if tem_valor:
                    valor_str = match_valor.group(1)
                    valor = limpar_valor(valor_str)
                    texto_conteudo = line_clean.replace(valor_str, "").strip()

                # --- NÍVEL 1: COMPLEXIDADE (USANDO LIMITE DINÂMICO) ---
                eh_titulo_complexidade = (x_inicio < LIMITE_NIVEL_1) and texto_conteudo.isupper() and len(texto_conteudo) > 3

                if eh_titulo_complexidade:
                    curr_complexidade = padronizar_complexidade(texto_conteudo)
                    curr_financiamento = ""
                    flag_cabecalho_recente = False
                    continue

                # --- NÍVEL 2: FINANCIAMENTO ---
                eh_novo_financiamento = False
                novo_finan_temp = ""

                if "fundo de acoes" in line_norm:
                    novo_finan_temp = "FAEC"
                    eh_novo_financiamento = True

                elif "media e alta complexidade" in line_norm:
                    novo_finan_temp = "MAC"
                    eh_novo_financiamento = True

                elif "pab" in line_norm:
                    novo_finan_temp = "PAB"
                    eh_novo_financiamento = True
                elif "vigilancia" in line_norm:
                    novo_finan_temp = "VIGILANCIA"
                    eh_novo_financiamento = True

                if eh_novo_financiamento:
                    curr_financiamento = novo_finan_temp
                    flag_cabecalho_recente = True

                    if tem_valor and valor > 0:
                        flag_cabecalho_recente = False
                        if novo_finan_temp == "MAC":
                            dados.append({
                                "Hospital/Prestador": hospital_oficial,
                                "Mês/Ano": competencia,
                                "Credor": "Hospital",
                                "Âmbito Serviço": "Ambulatorial",
                                "Complexidade": curr_complexidade,
                                "Financiamento": curr_financiamento,
                                "Subtipo FAEC": "BLMAC",
                                "Valor": valor
                            })
                    continue

                # --- NÍVEL 3: DADOS ---
                if tem_valor:
                    subtipo_final = "não possui"

                    # 1. Valor de cabeçalho (após mudança de financ)
                    if flag_cabecalho_recente and len(texto_conteudo) < 3:
                        flag_cabecalho_recente = False
                        if curr_financiamento == "MAC":
                            subtipo_final = "BLMAC"
                        else:
                            continue

                    # 2. Texto na própria linha
                    elif len(texto_conteudo) > 3:
                        subtipo_final = padronizar_subtipo(texto_conteudo)

                    # 3. Texto da fila (memória)
                    elif textos_pendentes:
                        texto_pendente = textos_pendentes.pop(0)
                        subtipo_final = padronizar_subtipo(texto_pendente)

                    # 4. Saldo do MAC
                    elif curr_financiamento == "MAC":
                        subtipo_final = "BLMAC"

                    if subtipo_final == "não possui": continue
                    if "TOTAL" in subtipo_final.upper(): continue

                    if curr_complexidade and valor > 0:
                        dados.append({
                            "Hospital/Prestador": hospital_oficial,
                            "Mês/Ano": competencia,
                            "Credor": "Hospital",
                            "Âmbito Serviço": "Ambulatorial",
                            "Complexidade": curr_complexidade,
                            "Financiamento": curr_financiamento,
                            "Subtipo FAEC": subtipo_final,
                            "Valor": valor
                        })

                # --- CAPTURA DE TEXTO ÓRFÃO ---
                elif not tem_valor and len(texto_conteudo) > 3:
                    if not any(x in line_norm for x in ["cpf", "cnpj", "total", "valores"]):
                        textos_pendentes.append(texto_conteudo)

    return dados

def executar_extracao_completa(lista_arquivos, callback_update):
    todos_dados = []
    total_arquivos = len(lista_arquivos)
    for i, arq in enumerate(lista_arquivos):
        nome_arq = os.path.basename(arq)
        progresso_atual = (i / total_arquivos)
        callback_update(f"Analisando: {nome_arq}...", progresso_atual)
        try:
            tipo_arquivo = detecting_tipo_relatorio(arq)
            if tipo_arquivo == "AMBULATORIAL":
                dados = processar_ambulatorial(arq)
            elif tipo_arquivo == "HOSPITALAR":
                dados = processar_hospitalar(arq)
            else:
                callback_update(f"Ignorado: {nome_arq} (Formato desconhecido)", progresso_atual)
                continue
            todos_dados.extend(dados)
        except Exception as e:
            print(f"ERRO REAL NO ARQUIVO {nome_arq}: {e}")
            callback_update(f"Erro em {nome_arq}: {str(e)}", progresso_atual)
    callback_update("Consolidando tabela...", 0.95)
    if todos_dados:
        df = pd.DataFrame(todos_dados)
        colunas_ordem = ["Hospital/Prestador", "Mês/Ano", "Credor", "Âmbito Serviço",
                         "Complexidade", "Financiamento", "Subtipo FAEC", "Valor"]
        for col in colunas_ordem:
            if col not in df.columns: df[col] = ""
        return df[colunas_ordem]
    else:
        return pd.DataFrame()

    #teste de push