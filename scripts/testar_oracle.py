"""
Teste de integração com o Oracle real.

Executa cada operação do sistema no banco e confere o resultado.
Usa IDs a partir de 900000 e apaga tudo no final, sem mexer nos dados do sistema.

Como executar (na pasta do projeto):
    python scripts/testar_oracle.py
"""

import os
import sys
from getpass import getpass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import banco      # noqa: E402
import calculos   # noqa: E402

ID_T, ID_C = 900001, 900001
resultados = []


def verificar(descricao, condicao):
    resultados.append(condicao)
    print(f"  [{'OK ' if condicao else 'ERRO'}] {descricao}")


def main():
    config = banco.ler_configuracao()
    usuario = config["usuario"] or input("Usuário Oracle (RM): ").strip()
    senha = config["senha"] or getpass("Senha Oracle: ")
    print(f"\nConectando a {config['dsn']}...")
    conexao = banco.conectar(usuario, senha, config["dsn"])
    verificar("Conexão e criação das tabelas", conexao is not None)
    if conexao is None:
        return

    try:
        talhao = {"id": ID_T, "nome": "TESTE AUTOMATICO", "area_ha": 10.0,
                  "variedade": "RB-TESTE", "produtividade_t_ha": 90.0}
        verificar("INSERT talhão", banco.inserir_talhao(conexao, talhao))
        lido = next((t for t in banco.listar_talhoes(conexao) if t["id"] == ID_T), None)
        verificar("SELECT talhão devolve os mesmos dados", lido == talhao)

        talhao["nome"], talhao["area_ha"] = "TESTE ALTERADO", 12.5
        verificar("UPDATE talhão", banco.atualizar_talhao(conexao, talhao))
        lido = next((t for t in banco.listar_talhoes(conexao) if t["id"] == ID_T), None)
        verificar("UPDATE gravado no banco", lido and lido["nome"] == "TESTE ALTERADO"
                  and lido["area_ha"] == 12.5)

        colheita = calculos.montar_colheita(ID_C, talhao, "15/08/2026", "Mecanizada", 1000.0, 150.0)
        verificar("INSERT colheita (com data e acentos)", banco.inserir_colheita(conexao, colheita))
        lida = next((c for c in banco.listar_colheitas(conexao) if c["id"] == ID_C), None)
        verificar("SELECT colheita devolve os mesmos dados", lida == colheita)

        print("  (o próximo teste deve mostrar um erro do banco, que é esperado)")
        invalida = dict(colheita, id=ID_C + 1, tipo="Drone")
        verificar("CHECK rejeita tipo de colheita inválido", not banco.inserir_colheita(conexao, invalida))

        verificar("Próximo ID calculado pelo banco",
                  banco.proximo_id_banco(conexao, "FT_COLHEITA", "ID_COLHEITA") > ID_C)

        verificar("DELETE talhão", banco.excluir_talhao(conexao, ID_T))
        restantes = [c for c in banco.listar_colheitas(conexao) if c["id"] == ID_C]
        verificar("ON DELETE CASCADE removeu a colheita do talhão", restantes == [])
    finally:
        banco.executar(conexao, "DELETE FROM FT_COLHEITA WHERE ID_COLHEITA >= 900000")
        banco.executar(conexao, "DELETE FROM FT_TALHAO WHERE ID_TALHAO >= 900000")
        banco.desconectar(conexao)

    print(f"\nResultado: {sum(resultados)} de {len(resultados)} testes OK.")


if __name__ == "__main__":
    main()
