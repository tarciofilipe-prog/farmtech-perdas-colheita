"""
Conexão e operações no banco de dados Oracle (biblioteca oracledb).

O sistema funciona em dois modos:
  - ONLINE: cada operação é gravada também no Oracle;
  - OFFLINE: sem conexão, os dados ficam em memória e no backup JSON.
"""

import json
import os

from constantes import ARQUIVO_CONFIG

try:
    import oracledb
except ImportError:  # biblioteca não instalada
    oracledb = None


DDL_TALHAO = """
CREATE TABLE FT_TALHAO (
    ID_TALHAO           NUMBER(6)        PRIMARY KEY,
    NOME                VARCHAR2(50 CHAR) NOT NULL,
    AREA_HA             NUMBER(10,2)     NOT NULL CHECK (AREA_HA > 0),
    VARIEDADE           VARCHAR2(30 CHAR),
    PRODUTIVIDADE_T_HA  NUMBER(8,2)      NOT NULL CHECK (PRODUTIVIDADE_T_HA > 0)
)"""

DDL_COLHEITA = """
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
)"""

SQL_INSERIR_TALHAO = """
INSERT INTO FT_TALHAO (ID_TALHAO, NOME, AREA_HA, VARIEDADE, PRODUTIVIDADE_T_HA)
VALUES (:id, :nome, :area_ha, :variedade, :produtividade_t_ha)"""

SQL_INSERIR_COLHEITA = """
INSERT INTO FT_COLHEITA (ID_COLHEITA, ID_TALHAO, DATA_COLHEITA, TIPO_COLHEITA,
                         TON_ESPERADA, TON_COLHIDA, PERDA_T, PERDA_PCT,
                         CLASSIFICACAO, PRECO_TON, PREJUIZO)
VALUES (:id, :id_talhao, TO_DATE(:data, 'DD/MM/YYYY'), :tipo,
        :ton_esperada, :ton_colhida, :perda_t, :perda_pct,
        :classificacao, :preco_ton, :prejuizo)"""


# ------------------------------------------------------------------------------
# Conexão
# ------------------------------------------------------------------------------
def ler_configuracao():
    """
    Lê usuário, senha e DSN de variáveis de ambiente ou do arquivo
    config/config_oracle.json. Devolve um dicionário.
    """
    config = {"usuario": "", "senha": "", "dsn": "oracle.fiap.com.br:1521/ORCL"}
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as arquivo:
                config.update(json.load(arquivo))
        except (OSError, json.JSONDecodeError):
            pass
    config["usuario"] = os.environ.get("ORACLE_USER", config["usuario"])
    config["senha"] = os.environ.get("ORACLE_PASSWORD", config["senha"])
    config["dsn"] = os.environ.get("ORACLE_DSN", config["dsn"])
    return config


def conectar(usuario, senha, dsn):
    """Abre a conexão com o Oracle. Devolve a conexão ou None se falhar."""
    if oracledb is None:
        print("  ✖ A biblioteca 'oracledb' não está instalada (pip install oracledb).")
        return None
    try:
        conexao = oracledb.connect(user=usuario, password=senha, dsn=dsn)
        criar_tabelas(conexao)
        return conexao
    except oracledb.Error as erro:
        print(f"  ✖ Não foi possível conectar ao Oracle: {erro}")
        return None


def desconectar(conexao):
    """Fecha a conexão, se existir."""
    if conexao is not None:
        try:
            conexao.close()
        except Exception:
            pass


def tabela_existe(cursor, nome_tabela):
    """Consulta o dicionário de dados do Oracle para saber se a tabela existe."""
    cursor.execute("SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = :nome",
                   nome=nome_tabela)
    return cursor.fetchone()[0] > 0


def criar_tabelas(conexao):
    """Cria as tabelas na primeira execução."""
    with conexao.cursor() as cursor:
        if not tabela_existe(cursor, "FT_TALHAO"):
            cursor.execute(DDL_TALHAO)
        if not tabela_existe(cursor, "FT_COLHEITA"):
            cursor.execute(DDL_COLHEITA)
    conexao.commit()


def executar(conexao, sql, parametros=None):
    """
    Executa um comando de escrita (INSERT/UPDATE/DELETE) com commit.
    Devolve True se der certo; em caso de erro faz rollback e devolve False.
    """
    if conexao is None:
        return True  # modo offline: nada a fazer no banco
    try:
        with conexao.cursor() as cursor:
            cursor.execute(sql, parametros or {})
        conexao.commit()
        return True
    except oracledb.Error as erro:
        conexao.rollback()
        print(f"  ✖ Erro no banco de dados: {erro}")
        return False


def proximo_id_banco(conexao, tabela, coluna):
    """Busca no banco o próximo ID livre (evita colisão com gravações de outra sessão)."""
    with conexao.cursor() as cursor:
        cursor.execute(f"SELECT NVL(MAX({coluna}), 0) + 1 FROM {tabela}")
        return int(cursor.fetchone()[0])


# ------------------------------------------------------------------------------
# CRUD - Talhões
# ------------------------------------------------------------------------------
def inserir_talhao(conexao, talhao):
    return executar(conexao, SQL_INSERIR_TALHAO, talhao)


def atualizar_talhao(conexao, talhao):
    sql = """
    UPDATE FT_TALHAO
       SET NOME = :nome, AREA_HA = :area_ha, VARIEDADE = :variedade,
           PRODUTIVIDADE_T_HA = :produtividade_t_ha
     WHERE ID_TALHAO = :id"""
    return executar(conexao, sql, talhao)


def excluir_talhao(conexao, id_talhao):
    # As colheitas do talhão são apagadas junto (ON DELETE CASCADE)
    return executar(conexao, "DELETE FROM FT_TALHAO WHERE ID_TALHAO = :id", {"id": id_talhao})


def listar_talhoes(conexao):
    """Devolve a lista de talhões gravados no banco (lista de dicionários)."""
    sql = """SELECT ID_TALHAO, NOME, AREA_HA, VARIEDADE, PRODUTIVIDADE_T_HA
               FROM FT_TALHAO ORDER BY ID_TALHAO"""
    with conexao.cursor() as cursor:
        cursor.execute(sql)
        return [
            {"id": int(l[0]), "nome": l[1], "area_ha": float(l[2]),
             "variedade": l[3] or "", "produtividade_t_ha": float(l[4])}
            for l in cursor.fetchall()
        ]


# ------------------------------------------------------------------------------
# CRUD - Colheitas
# ------------------------------------------------------------------------------
def inserir_colheita(conexao, colheita):
    return executar(conexao, SQL_INSERIR_COLHEITA, colheita)


def excluir_colheita(conexao, id_colheita):
    return executar(conexao, "DELETE FROM FT_COLHEITA WHERE ID_COLHEITA = :id",
                    {"id": id_colheita})


def listar_colheitas(conexao):
    """Devolve a lista de colheitas gravadas no banco (lista de dicionários)."""
    sql = """SELECT ID_COLHEITA, ID_TALHAO, TO_CHAR(DATA_COLHEITA, 'DD/MM/YYYY'),
                    TIPO_COLHEITA, TON_ESPERADA, TON_COLHIDA, PERDA_T, PERDA_PCT,
                    CLASSIFICACAO, PRECO_TON, PREJUIZO
               FROM FT_COLHEITA ORDER BY DATA_COLHEITA, ID_COLHEITA"""
    with conexao.cursor() as cursor:
        cursor.execute(sql)
        return [
            {"id": int(l[0]), "id_talhao": int(l[1]), "data": l[2], "tipo": l[3],
             "ton_esperada": float(l[4]), "ton_colhida": float(l[5]),
             "perda_t": float(l[6]), "perda_pct": float(l[7]),
             "classificacao": l[8], "preco_ton": float(l[9]), "prejuizo": float(l[10])}
            for l in cursor.fetchall()
        ]


def substituir_tudo(conexao, talhoes, colheitas):
    """
    Substitui todo o conteúdo das tabelas pelos dados informados
    (usado ao importar um JSON ou carregar dados de exemplo).
    Tudo em uma única transação: ou grava tudo, ou nada.
    """
    if conexao is None:
        return True
    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM FT_COLHEITA")
            cursor.execute("DELETE FROM FT_TALHAO")
            if talhoes:
                cursor.executemany(SQL_INSERIR_TALHAO, talhoes)
            if colheitas:
                cursor.executemany(SQL_INSERIR_COLHEITA, colheitas)
        conexao.commit()
        return True
    except oracledb.Error as erro:
        conexao.rollback()
        print(f"  ✖ Erro ao sincronizar com o banco: {erro}")
        return False
