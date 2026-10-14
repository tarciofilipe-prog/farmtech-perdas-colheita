"""
Constantes e tabelas de referência da solução.

Aqui ficam as estruturas que NÃO mudam durante a execução, por isso
usamos TUPLAS (imutáveis) e DICIONÁRIOS de consulta.
"""

import os

# ------------------------------------------------------------------------------
# Caminhos do projeto
# ------------------------------------------------------------------------------
PASTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DADOS = os.path.join(PASTA_BASE, "dados")
PASTA_LOGS = os.path.join(PASTA_BASE, "logs")
ARQUIVO_JSON = os.path.join(PASTA_DADOS, "colheitas.json")
ARQUIVO_LOG = os.path.join(PASTA_LOGS, "operacoes.log")
ARQUIVO_RELATORIO = os.path.join(PASTA_DADOS, "relatorio_perdas.txt")
ARQUIVO_CONFIG = os.path.join(PASTA_BASE, "config", "config_oracle.json")

# ------------------------------------------------------------------------------
# TUPLAS: valores fixos do domínio
# ------------------------------------------------------------------------------
# Tipos de colheita aceitos (usados no menu e validados no banco)
TIPOS_COLHEITA = ("Manual", "Mecanizada")

# Faixas de classificação da perda: (limite superior em %, classificação)
# Referência: na colheita manual a perda raramente passa de 5%;
# na mecanizada pode chegar a 15% (SOCICANA).
FAIXAS_PERDA = (
    (5.0, "ACEITÁVEL"),
    (10.0, "ATENÇÃO"),
    (100.0, "CRÍTICA"),
)

# Meta de perda que a fazenda busca atingir (nível da colheita manual)
META_PERDA_PCT = 5.0

# ------------------------------------------------------------------------------
# DICIONÁRIOS de consulta
# ------------------------------------------------------------------------------
# Perda máxima de referência por tipo de colheita (%)
REFERENCIA_PERDA = {
    "Manual": 5.0,
    "Mecanizada": 15.0,
}

# Recomendações por classificação e por tipo de colheita
RECOMENDACOES = {
    "ACEITÁVEL": {
        "Manual": ("Manter o padrão atual de corte e carregamento.",),
        "Mecanizada": ("Manter a regulagem atual da colhedora e registrar "
                       "os parâmetros como referência para os demais talhões.",),
    },
    "ATENÇÃO": {
        "Manual": ("Revisar o corte rente ao solo (tocos altos deixam cana no campo).",
                   "Conferir o recolhimento de canas soltas antes do carregamento."),
        "Mecanizada": ("Verificar a altura do corte de base da colhedora.",
                       "Reduzir a velocidade de deslocamento em áreas com cana acamada.",
                       "Checar a rotação do extrator primário (excesso lança "
                       "pedaços de cana junto com a palha)."),
    },
    "CRÍTICA": {
        "Manual": ("Treinar a equipe de corte e reforçar a fiscalização no talhão.",
                   "Reavaliar o ponto de maturação: colher fora do momento ideal "
                   "aumenta as perdas."),
        "Mecanizada": ("Fazer manutenção das facas do corte de base e dos rolos.",
                       "Ajustar o sincronismo entre colhedora e transbordo para "
                       "evitar queda de cana fora da caçamba.",
                       "Rever o planejamento do plantio: sulcos e espaçamento "
                       "precisam ser compatíveis com a colhedora.",
                       "Fazer uma amostragem de perdas no campo para identificar "
                       "a origem (toco, pedaços, cana inteira)."),
    },
}
