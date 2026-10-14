"""
Manipulação de arquivos: JSON (backup e intercâmbio dos dados) e
texto (log de operações e relatório).
"""

import json
import os
from datetime import datetime

from constantes import ARQUIVO_LOG


def garantir_pasta(caminho_arquivo):
    """Cria a pasta do arquivo se ela ainda não existir."""
    pasta = os.path.dirname(caminho_arquivo)
    if pasta:
        os.makedirs(pasta, exist_ok=True)


# ------------------------------------------------------------------------------
# JSON
# ------------------------------------------------------------------------------
def salvar_json(caminho, talhoes, colheitas):
    """Grava talhões e colheitas em um arquivo JSON. Devolve True se der certo."""
    garantir_pasta(caminho)
    conteudo = {
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "talhoes": talhoes,
        "colheitas": colheitas,
    }
    try:
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(conteudo, arquivo, ensure_ascii=False, indent=4)
        return True
    except OSError as erro:
        print(f"  ✖ Não foi possível gravar o JSON: {erro}")
        return False


def carregar_json(caminho):
    """
    Lê o arquivo JSON e devolve uma tupla (talhoes, colheitas).
    Devolve None se o arquivo não existir ou estiver com formato inválido.
    """
    if not os.path.exists(caminho):
        return None
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)
    except (OSError, json.JSONDecodeError) as erro:
        print(f"  ✖ Arquivo JSON inválido: {erro}")
        return None

    talhoes = conteudo.get("talhoes")
    colheitas = conteudo.get("colheitas")
    if not isinstance(talhoes, list) or not isinstance(colheitas, list):
        print("  ✖ O JSON não tem as listas 'talhoes' e 'colheitas'.")
        return None

    campos_talhao = ("id", "nome", "area_ha", "variedade", "produtividade_t_ha")
    campos_colheita = ("id", "id_talhao", "data", "tipo", "ton_esperada", "ton_colhida",
                       "perda_t", "perda_pct", "classificacao", "preco_ton", "prejuizo")
    for registro in talhoes:
        if not isinstance(registro, dict) or any(c not in registro for c in campos_talhao):
            print("  ✖ Há talhões com campos faltando no JSON.")
            return None
    for registro in colheitas:
        if not isinstance(registro, dict) or any(c not in registro for c in campos_colheita):
            print("  ✖ Há colheitas com campos faltando no JSON.")
            return None
    return talhoes, colheitas


# ------------------------------------------------------------------------------
# TEXTO
# ------------------------------------------------------------------------------
def registrar_log(mensagem):
    """Procedimento: acrescenta uma linha com data e hora ao log de operações."""
    garantir_pasta(ARQUIVO_LOG)
    momento = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    try:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as arquivo:
            arquivo.write(f"[{momento}] {mensagem}\n")
    except OSError:
        pass  # o log nunca deve interromper o uso do sistema


def ler_ultimas_linhas_log(quantidade=15):
    """Devolve as últimas linhas do log de operações."""
    if not os.path.exists(ARQUIVO_LOG):
        return []
    with open(ARQUIVO_LOG, "r", encoding="utf-8") as arquivo:
        linhas = arquivo.readlines()
    return [linha.rstrip("\n") for linha in linhas[-quantidade:]]


def salvar_relatorio_txt(caminho, linhas):
    """Procedimento: grava as linhas de um relatório em um arquivo texto."""
    garantir_pasta(caminho)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        for linha in linhas:
            arquivo.write(linha + "\n")
