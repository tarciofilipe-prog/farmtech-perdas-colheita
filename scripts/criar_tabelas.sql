-- =============================================================================
-- FarmTech Solutions - Monitor de Perdas na Colheita de Cana
-- Script de criação das tabelas (Oracle)
-- Obs.: o programa cria as tabelas automaticamente na primeira conexão.
--       Este script serve para criar manualmente ou para conferência.
-- =============================================================================

CREATE TABLE FT_TALHAO (
    ID_TALHAO           NUMBER(6)         PRIMARY KEY,
    NOME                VARCHAR2(50 CHAR) NOT NULL,
    AREA_HA             NUMBER(10,2)      NOT NULL CHECK (AREA_HA > 0),
    VARIEDADE           VARCHAR2(30 CHAR),
    PRODUTIVIDADE_T_HA  NUMBER(8,2)       NOT NULL CHECK (PRODUTIVIDADE_T_HA > 0)
);

CREATE TABLE FT_COLHEITA (
    ID_COLHEITA     NUMBER(8)         PRIMARY KEY,
    ID_TALHAO       NUMBER(6)         NOT NULL
                    REFERENCES FT_TALHAO (ID_TALHAO) ON DELETE CASCADE,
    DATA_COLHEITA   DATE              NOT NULL,
    TIPO_COLHEITA   VARCHAR2(10 CHAR) NOT NULL
                    CHECK (TIPO_COLHEITA IN ('Manual', 'Mecanizada')),
    TON_ESPERADA    NUMBER(12,2)      NOT NULL,
    TON_COLHIDA     NUMBER(12,2)      NOT NULL,
    PERDA_T         NUMBER(12,2)      NOT NULL,
    PERDA_PCT       NUMBER(5,2)       NOT NULL,
    CLASSIFICACAO   VARCHAR2(20 CHAR) NOT NULL,
    PRECO_TON       NUMBER(10,2)      NOT NULL,
    PREJUIZO        NUMBER(14,2)      NOT NULL
);

-- Consulta de apoio: perda média por tipo de colheita
SELECT TIPO_COLHEITA,
       COUNT(*)                                       AS COLHEITAS,
       ROUND(SUM(PERDA_T) / SUM(TON_ESPERADA) * 100, 2) AS PERDA_MEDIA_PCT,
       SUM(PREJUIZO)                                  AS PREJUIZO_TOTAL
  FROM FT_COLHEITA
 GROUP BY TIPO_COLHEITA;

-- Para remover as tabelas:
-- DROP TABLE FT_COLHEITA;
-- DROP TABLE FT_TALHAO;
