"""
Regras de negócio: cálculo, classificação e recomendações sobre as perdas
na colheita da cana-de-açúcar.
"""

from constantes import FAIXAS_PERDA, META_PERDA_PCT, RECOMENDACOES, REFERENCIA_PERDA


def calcular_producao_esperada(area_ha, produtividade_t_ha):
    """Produção esperada do talhão em toneladas."""
    return round(area_ha * produtividade_t_ha, 2)


def calcular_perda(producao_esperada, producao_colhida):
    """
    Devolve uma TUPLA (perda em toneladas, perda em %).
    Se a colheita superar o esperado, a perda é zero.
    """
    perda_t = max(producao_esperada - producao_colhida, 0.0)
    perda_pct = (perda_t / producao_esperada) * 100 if producao_esperada > 0 else 0.0
    return round(perda_t, 2), round(perda_pct, 2)


def classificar_perda(perda_pct):
    """Percorre a tupla de faixas e devolve a classificação da perda."""
    for limite, classificacao in FAIXAS_PERDA:
        if perda_pct <= limite:
            return classificacao
    return FAIXAS_PERDA[-1][1]


def calcular_prejuizo(perda_t, preco_tonelada):
    """Valor financeiro perdido (R$)."""
    return round(perda_t * preco_tonelada, 2)


def calcular_economia_potencial(producao_esperada, perda_pct, preco_tonelada):
    """
    Quanto o produtor deixaria de perder (R$) se a perda caísse para a meta.
    Se já estiver dentro da meta, a economia é zero.
    """
    if perda_pct <= META_PERDA_PCT:
        return 0.0
    toneladas_recuperaveis = producao_esperada * (perda_pct - META_PERDA_PCT) / 100
    return round(toneladas_recuperaveis * preco_tonelada, 2)


def obter_recomendacoes(classificacao, tipo_colheita):
    """Consulta o dicionário de recomendações e devolve uma lista de ações."""
    return list(RECOMENDACOES.get(classificacao, {}).get(tipo_colheita, ()))


def montar_colheita(id_colheita, talhao, data, tipo, toneladas_colhidas, preco_tonelada):
    """Cria o dicionário de uma colheita com todos os indicadores calculados."""
    esperada = calcular_producao_esperada(talhao["area_ha"], talhao["produtividade_t_ha"])
    perda_t, perda_pct = calcular_perda(esperada, toneladas_colhidas)
    classificacao = classificar_perda(perda_pct)
    return {
        "id": id_colheita,
        "id_talhao": talhao["id"],
        "data": data,
        "tipo": tipo,
        "ton_esperada": esperada,
        "ton_colhida": toneladas_colhidas,
        "perda_t": perda_t,
        "perda_pct": perda_pct,
        "classificacao": classificacao,
        "preco_ton": preco_tonelada,
        "prejuizo": calcular_prejuizo(perda_t, preco_tonelada),
    }


def comparar_com_referencia(tipo_colheita, perda_pct):
    """Diz se a perda está acima ou abaixo da referência do tipo de colheita."""
    referencia = REFERENCIA_PERDA[tipo_colheita]
    if perda_pct > referencia:
        return f"acima da referência de {referencia:.0f}% para colheita {tipo_colheita.lower()}"
    return f"dentro da referência de {referencia:.0f}% para colheita {tipo_colheita.lower()}"
