"""
================================================================================
 FarmTech Solutions - Monitor de Perdas na Colheita de Cana-de-Açúcar
================================================================================
Problema tratado: as perdas na colheita da cana chegam a 15% na colheita
mecanizada, contra cerca de 5% na manual. O sistema registra as colheitas
de cada talhão, calcula a perda em toneladas, em % e em reais, classifica
o talhão e sugere ações para reduzir a perda.

Como executar:  python src/main.py
================================================================================
"""

from getpass import getpass

import arquivos
import banco
import calculos
from constantes import (ARQUIVO_JSON, ARQUIVO_RELATORIO, FAIXAS_PERDA,
                        META_PERDA_PCT, TIPOS_COLHEITA)
from validacao import (confirmar, ler_data, ler_decimal, ler_inteiro, ler_opcao,
                       ler_texto)

# ==============================================================================
# Estado da aplicação (dados em memória)
# ==============================================================================
# LISTAS de DICIONÁRIOS: cada dicionário é um registro (talhão ou colheita)
talhoes = []
colheitas = []
conexao = None  # conexão Oracle (None = modo offline)

LARGURA = 78


# ==============================================================================
# Apresentação no terminal
# ==============================================================================
def formatar_numero(valor, casas=2):
    """Formata número no padrão brasileiro: 1.234,56"""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_reais(valor):
    return "R$ " + formatar_numero(valor)


def titulo(texto):
    """Procedimento: imprime um título de seção."""
    print("\n" + "=" * LARGURA)
    print(f" {texto}")
    print("=" * LARGURA)


def montar_tabela_texto(cabecalho, linhas):
    """
    Recebe o cabeçalho (tupla) e as linhas (tabela de memória: lista de listas)
    e devolve uma lista de strings com as colunas alinhadas.
    """
    larguras = [len(str(c)) for c in cabecalho]
    for linha in linhas:
        for i, celula in enumerate(linha):
            larguras[i] = max(larguras[i], len(str(celula)))

    def formatar_linha(celulas):
        partes = []
        for i, celula in enumerate(celulas):
            texto = str(celula)
            # números à direita, textos à esquerda
            if texto.replace(".", "").replace(",", "").replace("%", "") \
                    .replace("R$ ", "").replace("-", "").strip().isdigit():
                partes.append(texto.rjust(larguras[i]))
            else:
                partes.append(texto.ljust(larguras[i]))
        return " | ".join(partes)

    separador = "-+-".join("-" * l for l in larguras)
    resultado = [formatar_linha(cabecalho), separador]
    resultado.extend(formatar_linha(linha) for linha in linhas)
    return resultado


def imprimir_tabela(cabecalho, linhas):
    """Procedimento: imprime uma tabela de memória alinhada."""
    for linha in montar_tabela_texto(cabecalho, linhas):
        print(" " + linha)


def pausar():
    input("\nPressione ENTER para voltar ao menu...")


# ==============================================================================
# Consultas em memória
# ==============================================================================
def proximo_id(registros, tabela=None, coluna=None):
    """
    Gera o próximo ID. No modo online consulta também o banco, para não
    colidir com registros gravados por outra sessão.
    """
    maior_memoria = max((r["id"] for r in registros), default=0) + 1
    if conexao is not None and tabela:
        try:
            return max(maior_memoria, banco.proximo_id_banco(conexao, tabela, coluna))
        except Exception:
            pass
    return maior_memoria


def buscar_por_id(registros, id_procurado):
    """Devolve o dicionário com o ID informado, ou None."""
    for registro in registros:
        if registro["id"] == id_procurado:
            return registro
    return None


def nome_do_talhao(id_talhao):
    talhao = buscar_por_id(talhoes, id_talhao)
    return talhao["nome"] if talhao else "(removido)"


def escolher_registro(registros, descricao):
    """Pede o ID de um registro existente. Devolve o registro ou None (cancelar)."""
    if not registros:
        print(f"\nNenhum {descricao} cadastrado.")
        return None
    while True:
        id_digitado = ler_inteiro(f"\nInforme o ID do {descricao} (0 para cancelar): ", 0)
        if id_digitado == 0:
            return None
        registro = buscar_por_id(registros, id_digitado)
        if registro:
            return registro
        print(f"  ⚠ Não existe {descricao} com o ID {id_digitado}.")


def salvar_backup():
    """Mantém o JSON sempre atualizado como cópia de segurança."""
    arquivos.salvar_json(ARQUIVO_JSON, talhoes, colheitas)


# ==============================================================================
# Talhões
# ==============================================================================
def ler_dados_talhao(atual=None):
    """Lê os dados de um talhão. Em uma atualização, mostra o valor atual."""
    def rotulo(texto, campo):
        return f"{texto} [atual: {atual[campo]}]: " if atual else f"{texto}: "

    return {
        "nome": ler_texto(rotulo("Nome do talhão", "nome"), 50),
        "area_ha": ler_decimal(rotulo("Área (hectares)", "area_ha"), maximo=100000),
        "variedade": ler_texto(rotulo("Variedade da cana (ex.: RB867515)", "variedade"),
                               30, obrigatorio=False),
        "produtividade_t_ha": ler_decimal(
            rotulo("Produtividade esperada (t/ha, normalmente 60 a 120)",
                   "produtividade_t_ha"), maximo=300),
    }


def cadastrar_talhao():
    titulo("CADASTRAR TALHÃO")
    dados = ler_dados_talhao()
    nomes_existentes = [t["nome"].lower() for t in talhoes]
    if dados["nome"].lower() in nomes_existentes:
        print("  ⚠ Já existe um talhão com esse nome. Cadastro cancelado.")
        return

    talhao = {"id": proximo_id(talhoes, "FT_TALHAO", "ID_TALHAO"), **dados}
    if not banco.inserir_talhao(conexao, talhao):
        return
    talhoes.append(talhao)
    salvar_backup()
    arquivos.registrar_log(f"Talhão cadastrado: ID {talhao['id']} - {talhao['nome']}")

    esperada = calculos.calcular_producao_esperada(talhao["area_ha"], talhao["produtividade_t_ha"])
    print(f"\n  ✔ Talhão '{talhao['nome']}' cadastrado com o ID {talhao['id']}.")
    print(f"    Produção esperada: {formatar_numero(esperada)} toneladas.")


def listar_talhoes():
    titulo("TALHÕES CADASTRADOS")
    if not talhoes:
        print("Nenhum talhão cadastrado.")
        return
    tabela = []
    for t in talhoes:
        tabela.append([
            t["id"], t["nome"], t["variedade"] or "-",
            formatar_numero(t["area_ha"]),
            formatar_numero(t["produtividade_t_ha"]),
            formatar_numero(calculos.calcular_producao_esperada(t["area_ha"],
                                                                t["produtividade_t_ha"])),
            sum(1 for c in colheitas if c["id_talhao"] == t["id"]),
        ])
    imprimir_tabela(("ID", "Talhão", "Variedade", "Área (ha)", "Prod. (t/ha)",
                     "Esperado (t)", "Colheitas"), tabela)


def atualizar_talhao():
    titulo("ATUALIZAR TALHÃO")
    listar_talhoes()
    talhao = escolher_registro(talhoes, "talhão")
    if talhao is None:
        return
    print("\nDigite os novos dados:")
    novos = {"id": talhao["id"], **ler_dados_talhao(talhao)}
    if any(t["nome"].lower() == novos["nome"].lower() and t["id"] != talhao["id"]
           for t in talhoes):
        print("  ⚠ Já existe outro talhão com esse nome. Atualização cancelada.")
        return
    if not banco.atualizar_talhao(conexao, novos):
        return
    talhao.update(novos)
    salvar_backup()
    arquivos.registrar_log(f"Talhão atualizado: ID {talhao['id']} - {talhao['nome']}")
    print("\n  ✔ Talhão atualizado. As colheitas já registradas mantêm os valores "
          "calculados na data da colheita.")


def excluir_talhao():
    global colheitas
    titulo("EXCLUIR TALHÃO")
    listar_talhoes()
    talhao = escolher_registro(talhoes, "talhão")
    if talhao is None:
        return
    qtd = sum(1 for c in colheitas if c["id_talhao"] == talhao["id"])
    aviso = f" e suas {qtd} colheita(s)" if qtd else ""
    if not confirmar(f"Confirma a exclusão do talhão '{talhao['nome']}'{aviso}?"):
        print("Exclusão cancelada.")
        return
    if not banco.excluir_talhao(conexao, talhao["id"]):
        return
    talhoes.remove(talhao)
    colheitas = [c for c in colheitas if c["id_talhao"] != talhao["id"]]
    salvar_backup()
    arquivos.registrar_log(f"Talhão excluído: ID {talhao['id']} - {talhao['nome']}")
    print("\n  ✔ Talhão excluído.")


# ==============================================================================
# Colheitas
# ==============================================================================
def exibir_diagnostico(colheita):
    """Procedimento: mostra o resultado e as recomendações de uma colheita."""
    print("\n" + "-" * LARGURA)
    print(f" Talhão ............: {nome_do_talhao(colheita['id_talhao'])}")
    print(f" Data / tipo .......: {colheita['data']} - colheita {colheita['tipo'].lower()}")
    print(f" Produção esperada .: {formatar_numero(colheita['ton_esperada'])} t")
    print(f" Produção colhida ..: {formatar_numero(colheita['ton_colhida'])} t")
    print(f" Perda .............: {formatar_numero(colheita['perda_t'])} t "
          f"({formatar_numero(colheita['perda_pct'])}%)")
    print(f" Prejuízo estimado .: {formatar_reais(colheita['prejuizo'])}")
    print(f" Classificação .....: {colheita['classificacao']} "
          f"({calculos.comparar_com_referencia(colheita['tipo'], colheita['perda_pct'])})")
    economia = calculos.calcular_economia_potencial(
        colheita["ton_esperada"], colheita["perda_pct"], colheita["preco_ton"])
    if economia > 0:
        print(f" Economia possível .: {formatar_reais(economia)} se a perda cair para "
              f"{META_PERDA_PCT:.0f}%")
    print("\n Recomendações:")
    for acao in calculos.obter_recomendacoes(colheita["classificacao"], colheita["tipo"]):
        print(f"   • {acao}")
    print("-" * LARGURA)


def registrar_colheita():
    titulo("REGISTRAR COLHEITA")
    if not talhoes:
        print("Cadastre um talhão antes de registrar colheitas.")
        return
    listar_talhoes()
    talhao = escolher_registro(talhoes, "talhão")
    if talhao is None:
        return

    data = ler_data("Data da colheita (dd/mm/aaaa): ")
    tipo = ler_opcao("Tipo de colheita:", TIPOS_COLHEITA)
    esperada = calculos.calcular_producao_esperada(talhao["area_ha"], talhao["produtividade_t_ha"])
    print(f"(Produção esperada para este talhão: {formatar_numero(esperada)} t)")
    colhida = ler_decimal("Toneladas efetivamente colhidas: ", maximo=esperada * 2)
    preco = ler_decimal("Preço pago pela tonelada de cana (R$): ", maximo=10000)

    colheita = calculos.montar_colheita(proximo_id(colheitas, "FT_COLHEITA", "ID_COLHEITA"), talhao, data, tipo,
                                        colhida, preco)
    if not banco.inserir_colheita(conexao, colheita):
        return
    colheitas.append(colheita)
    salvar_backup()
    arquivos.registrar_log(
        f"Colheita registrada: ID {colheita['id']} - talhão {talhao['nome']} - "
        f"perda {formatar_numero(colheita['perda_pct'])}% ({colheita['classificacao']})")
    print("\n  ✔ Colheita registrada.")
    exibir_diagnostico(colheita)


def montar_tabela_colheitas(lista):
    """Converte a lista de dicionários em tabela de memória (lista de listas)."""
    return [
        [c["id"], nome_do_talhao(c["id_talhao"]), c["data"], c["tipo"],
         formatar_numero(c["ton_esperada"]), formatar_numero(c["ton_colhida"]),
         formatar_numero(c["perda_pct"]) + "%", c["classificacao"],
         formatar_reais(c["prejuizo"])]
        for c in lista
    ]


CABECALHO_COLHEITAS = ("ID", "Talhão", "Data", "Tipo", "Esperado (t)", "Colhido (t)",
                       "Perda", "Situação", "Prejuízo")


def listar_colheitas():
    titulo("COLHEITAS REGISTRADAS")
    if not colheitas:
        print("Nenhuma colheita registrada.")
        return
    imprimir_tabela(CABECALHO_COLHEITAS, montar_tabela_colheitas(colheitas))


def detalhar_colheita():
    titulo("DIAGNÓSTICO DE UMA COLHEITA")
    listar_colheitas()
    colheita = escolher_registro(colheitas, "registro de colheita")
    if colheita:
        exibir_diagnostico(colheita)


def excluir_colheita():
    titulo("EXCLUIR COLHEITA")
    listar_colheitas()
    colheita = escolher_registro(colheitas, "registro de colheita")
    if colheita is None:
        return
    if not confirmar(f"Confirma a exclusão da colheita {colheita['id']}?"):
        print("Exclusão cancelada.")
        return
    if not banco.excluir_colheita(conexao, colheita["id"]):
        return
    colheitas.remove(colheita)
    salvar_backup()
    arquivos.registrar_log(f"Colheita excluída: ID {colheita['id']}")
    print("\n  ✔ Colheita excluída.")


# ==============================================================================
# Painel de perdas (relatório gerencial)
# ==============================================================================
def gerar_painel():
    """
    Função: monta o relatório gerencial e devolve uma lista de linhas de texto,
    usada tanto para exibir na tela quanto para gravar em arquivo.
    """
    linhas = []
    total_esperado = sum(c["ton_esperada"] for c in colheitas)
    total_perda = sum(c["perda_t"] for c in colheitas)
    total_prejuizo = sum(c["prejuizo"] for c in colheitas)
    perda_media = (total_perda / total_esperado * 100) if total_esperado else 0
    economia = sum(calculos.calcular_economia_potencial(c["ton_esperada"], c["perda_pct"],
                                                        c["preco_ton"]) for c in colheitas)

    linhas.append("RESUMO GERAL")
    linhas.append(f"  Colheitas analisadas ........: {len(colheitas)}")
    linhas.append(f"  Produção esperada ...........: {formatar_numero(total_esperado)} t")
    linhas.append(f"  Cana perdida no campo .......: {formatar_numero(total_perda)} t "
                  f"({formatar_numero(perda_media)}%)")
    linhas.append(f"  Prejuízo total estimado .....: {formatar_reais(total_prejuizo)}")
    linhas.append(f"  Economia se perda ≤ {META_PERDA_PCT:.0f}% ......: {formatar_reais(economia)}")

    # Comparativo por tipo de colheita (dicionário de acumuladores)
    por_tipo = {tipo: {"qtd": 0, "esperado": 0.0, "perda": 0.0, "prejuizo": 0.0}
                for tipo in TIPOS_COLHEITA}
    for c in colheitas:
        acumulador = por_tipo[c["tipo"]]
        acumulador["qtd"] += 1
        acumulador["esperado"] += c["ton_esperada"]
        acumulador["perda"] += c["perda_t"]
        acumulador["prejuizo"] += c["prejuizo"]

    tabela_tipo = []
    for tipo, a in por_tipo.items():
        pct = (a["perda"] / a["esperado"] * 100) if a["esperado"] else 0
        tabela_tipo.append([tipo, a["qtd"], formatar_numero(a["perda"]),
                            formatar_numero(pct) + "%", formatar_reais(a["prejuizo"])])
    linhas.append("")
    linhas.append("COMPARATIVO MANUAL x MECANIZADA")
    linhas.extend("  " + l for l in montar_tabela_texto(
        ("Tipo", "Colheitas", "Perda (t)", "Perda média", "Prejuízo"), tabela_tipo))

    # Distribuição por classificação
    linhas.append("")
    linhas.append("DISTRIBUIÇÃO POR SITUAÇÃO")
    for _, classificacao in FAIXAS_PERDA:
        qtd = sum(1 for c in colheitas if c["classificacao"] == classificacao)
        barra = "█" * qtd
        linhas.append(f"  {classificacao:<10} {qtd:>3}  {barra}")

    # Ranking: tabela de memória ordenada pelo prejuízo
    ranking = sorted(colheitas, key=lambda c: c["prejuizo"], reverse=True)[:5]
    linhas.append("")
    linhas.append("RANKING - MAIORES PREJUÍZOS")
    linhas.extend("  " + l for l in montar_tabela_texto(CABECALHO_COLHEITAS,
                                                         montar_tabela_colheitas(ranking)))

    # Talhões que precisam de ação
    criticos = [c for c in colheitas if c["classificacao"] != "ACEITÁVEL"]
    linhas.append("")
    linhas.append("PLANO DE AÇÃO")
    if not criticos:
        linhas.append("  Todas as colheitas estão dentro da meta. Nenhuma ação necessária.")
    for c in sorted(criticos, key=lambda c: c["perda_pct"], reverse=True):
        linhas.append(f"  {nome_do_talhao(c['id_talhao'])} ({c['data']}, {c['tipo'].lower()}, "
                      f"{formatar_numero(c['perda_pct'])}% - {c['classificacao']}):")
        for acao in calculos.obter_recomendacoes(c["classificacao"], c["tipo"]):
            linhas.append(f"    • {acao}")
    return linhas


def exibir_painel():
    titulo("PAINEL DE PERDAS NA COLHEITA")
    if not colheitas:
        print("Registre colheitas para visualizar o painel.")
        return
    for linha in gerar_painel():
        print(" " + linha)


# ==============================================================================
# Arquivos
# ==============================================================================
def exportar_json():
    titulo("EXPORTAR DADOS PARA JSON")
    if arquivos.salvar_json(ARQUIVO_JSON, talhoes, colheitas):
        arquivos.registrar_log("Dados exportados para JSON")
        print(f"  ✔ {len(talhoes)} talhão(ões) e {len(colheitas)} colheita(s) gravados em:")
        print(f"    {ARQUIVO_JSON}")


def limpar_registros(talhoes_lidos, colheitas_lidas):
    """Mantém só os campos esperados, com os tipos corretos (evita lixo do JSON)."""
    try:
        talhoes_ok = [{"id": int(t["id"]), "nome": str(t["nome"])[:50],
                       "area_ha": float(t["area_ha"]), "variedade": str(t["variedade"])[:30],
                       "produtividade_t_ha": float(t["produtividade_t_ha"])}
                      for t in talhoes_lidos]
        ids_talhoes = {t["id"] for t in talhoes_ok}
        colheitas_ok = [{"id": int(c["id"]), "id_talhao": int(c["id_talhao"]),
                         "data": str(c["data"]), "tipo": str(c["tipo"]),
                         "ton_esperada": float(c["ton_esperada"]),
                         "ton_colhida": float(c["ton_colhida"]),
                         "perda_t": float(c["perda_t"]), "perda_pct": float(c["perda_pct"]),
                         "classificacao": str(c["classificacao"]),
                         "preco_ton": float(c["preco_ton"]), "prejuizo": float(c["prejuizo"])}
                        for c in colheitas_lidas if int(c["id_talhao"]) in ids_talhoes]
    except (TypeError, ValueError):
        print("  ✖ O JSON contém valores com tipo inválido.")
        return None
    if any(c["tipo"] not in TIPOS_COLHEITA for c in colheitas_ok):
        print("  ✖ O JSON contém tipo de colheita inválido.")
        return None
    return talhoes_ok, colheitas_ok


def importar_json():
    global talhoes, colheitas
    titulo("IMPORTAR DADOS DE JSON")
    lido = arquivos.carregar_json(ARQUIVO_JSON)
    if lido is None:
        print(f"  Nenhum arquivo válido encontrado em {ARQUIVO_JSON}")
        return
    limpos = limpar_registros(*lido)
    if limpos is None:
        return
    novos_talhoes, novas_colheitas = limpos
    print(f"  O arquivo tem {len(novos_talhoes)} talhão(ões) e {len(novas_colheitas)} colheita(s).")
    if not confirmar("Substituir os dados atuais por estes?"):
        print("Importação cancelada.")
        return
    if not banco.substituir_tudo(conexao, novos_talhoes, novas_colheitas):
        return
    talhoes, colheitas = novos_talhoes, novas_colheitas
    arquivos.registrar_log("Dados importados do JSON")
    print("  ✔ Dados importados" + (" e gravados no Oracle." if conexao else "."))


def exportar_relatorio_txt():
    titulo("EXPORTAR RELATÓRIO EM TEXTO")
    if not colheitas:
        print("Registre colheitas antes de gerar o relatório.")
        return
    from datetime import datetime
    cabecalho = ["=" * LARGURA,
                 " FARMTECH SOLUTIONS - RELATÓRIO DE PERDAS NA COLHEITA DE CANA",
                 f" Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                 "=" * LARGURA, ""]
    arquivos.salvar_relatorio_txt(ARQUIVO_RELATORIO, cabecalho + gerar_painel())
    arquivos.registrar_log("Relatório TXT gerado")
    print(f"  ✔ Relatório gravado em: {ARQUIVO_RELATORIO}")


def exibir_log():
    titulo("HISTÓRICO DE OPERAÇÕES (últimas 15)")
    linhas = arquivos.ler_ultimas_linhas_log()
    if not linhas:
        print("Nenhuma operação registrada ainda.")
    for linha in linhas:
        print(" " + linha)


# ==============================================================================
# Dados de exemplo
# ==============================================================================
def carregar_exemplos():
    global talhoes, colheitas
    titulo("CARREGAR DADOS DE EXEMPLO")
    if (talhoes or colheitas) and not confirmar("Isso substitui os dados atuais. Continuar?"):
        return

    novos_talhoes = [
        {"id": 1, "nome": "Talhão Santa Rita", "area_ha": 45.0,
         "variedade": "RB867515", "produtividade_t_ha": 95.0},
        {"id": 2, "nome": "Talhão Boa Vista", "area_ha": 62.5,
         "variedade": "CTC4", "produtividade_t_ha": 88.0},
        {"id": 3, "nome": "Talhão Água Limpa", "area_ha": 30.0,
         "variedade": "RB966928", "produtividade_t_ha": 102.0},
        {"id": 4, "nome": "Talhão São José", "area_ha": 18.0,
         "variedade": "SP81-3250", "produtividade_t_ha": 80.0},
    ]
    # (talhão, data, tipo, toneladas colhidas, preço R$/t) -> tuplas imutáveis
    lancamentos = (
        (1, "10/05/2026", "Mecanizada", 3720.0, 150.0),
        (2, "22/05/2026", "Mecanizada", 4950.0, 150.0),
        (3, "03/06/2026", "Manual", 2950.0, 150.0),
        (4, "18/06/2026", "Manual", 1390.0, 150.0),
        (1, "15/08/2026", "Mecanizada", 4020.0, 155.0),
        (2, "02/09/2026", "Mecanizada", 5180.0, 155.0),
    )
    novas_colheitas = []
    for id_talhao, data, tipo, colhida, preco in lancamentos:
        talhao = buscar_por_id(novos_talhoes, id_talhao)
        novas_colheitas.append(calculos.montar_colheita(len(novas_colheitas) + 1, talhao,
                                                        data, tipo, colhida, preco))

    if not banco.substituir_tudo(conexao, novos_talhoes, novas_colheitas):
        return
    talhoes, colheitas = novos_talhoes, novas_colheitas
    salvar_backup()
    arquivos.registrar_log("Dados de exemplo carregados")
    print(f"  ✔ {len(talhoes)} talhões e {len(colheitas)} colheitas de exemplo carregados.")


# ==============================================================================
# Inicialização e menu
# ==============================================================================
def iniciar_conexao():
    """Tenta conectar ao Oracle e carrega os dados do banco ou do backup JSON."""
    global conexao, talhoes, colheitas
    titulo("FARMTECH SOLUTIONS - Monitor de Perdas na Colheita de Cana")
    config = banco.ler_configuracao()

    if confirmar("Deseja conectar ao banco de dados Oracle?"):
        usuario = config["usuario"] or ler_texto("Usuário Oracle (ex.: RM123456): ", 30)
        senha = config["senha"] or getpass("Senha Oracle: ")
        print(f"Conectando a {config['dsn']}...")
        conexao = banco.conectar(usuario, senha, config["dsn"])

    if conexao is not None:
        talhoes = banco.listar_talhoes(conexao)
        colheitas = banco.listar_colheitas(conexao)
        print(f"  ✔ Conectado ao Oracle. {len(talhoes)} talhão(ões) e "
              f"{len(colheitas)} colheita(s) carregados do banco.")
        arquivos.registrar_log("Sistema iniciado em modo ONLINE (Oracle)")
    else:
        print("  ▸ Modo OFFLINE: os dados ficam em memória e no arquivo JSON.")
        lido = arquivos.carregar_json(ARQUIVO_JSON)
        limpos = limpar_registros(*lido) if lido else None
        if limpos:
            talhoes, colheitas = limpos
            print(f"    Backup carregado: {len(talhoes)} talhão(ões) e "
                  f"{len(colheitas)} colheita(s).")
        arquivos.registrar_log("Sistema iniciado em modo OFFLINE")


# TUPLA de opções do menu: (tecla, descrição, função)
OPCOES_MENU = (
    ("1", "Cadastrar talhão", cadastrar_talhao),
    ("2", "Listar talhões", listar_talhoes),
    ("3", "Atualizar talhão", atualizar_talhao),
    ("4", "Excluir talhão", excluir_talhao),
    ("5", "Registrar colheita", registrar_colheita),
    ("6", "Listar colheitas", listar_colheitas),
    ("7", "Diagnóstico de uma colheita", detalhar_colheita),
    ("8", "Excluir colheita", excluir_colheita),
    ("9", "Painel de perdas", exibir_painel),
    ("10", "Exportar dados (JSON)", exportar_json),
    ("11", "Importar dados (JSON)", importar_json),
    ("12", "Exportar relatório (TXT)", exportar_relatorio_txt),
    ("13", "Histórico de operações (log)", exibir_log),
    ("14", "Carregar dados de exemplo", carregar_exemplos),
)


def exibir_menu():
    modo = "ONLINE - Oracle" if conexao else "OFFLINE - JSON"
    print("\n" + "=" * LARGURA)
    print(f" MENU PRINCIPAL{'':<40}[{modo}]")
    print("=" * LARGURA)
    grupos = (("TALHÕES", OPCOES_MENU[0:4]),
              ("COLHEITAS", OPCOES_MENU[4:8]),
              ("RELATÓRIOS E ARQUIVOS", OPCOES_MENU[8:]))
    for nome_grupo, opcoes in grupos:
        print(f" {nome_grupo}")
        for tecla, descricao, _ in opcoes:
            print(f"   {tecla:>2} - {descricao}")
    print("\n    0 - Sair")


def main():
    acoes = {tecla: funcao for tecla, _, funcao in OPCOES_MENU}  # dicionário de despacho
    try:
        iniciar_conexao()
        while True:
            exibir_menu()
            opcao = input("\nEscolha uma opção: ").strip()
            if opcao == "0":
                break
            acao = acoes.get(opcao)
            if acao is None:
                print("  ⚠ Opção inválida. Digite um dos números do menu.")
                continue
            acao()
            pausar()
    except (KeyboardInterrupt, EOFError):
        print("\n\nExecução interrompida pelo usuário.")
    finally:
        salvar_backup()
        banco.desconectar(conexao)
        arquivos.registrar_log("Sistema encerrado")
        print("\nDados salvos. Até a próxima safra!")


if __name__ == "__main__":
    main()
