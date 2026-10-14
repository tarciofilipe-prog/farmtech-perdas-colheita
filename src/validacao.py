"""
Funções de entrada de dados com validação.

Cada função repete a pergunta até o usuário digitar um valor válido,
evitando que um tipo indesejado chegue aos cálculos ou ao banco de dados.
"""

from datetime import datetime


def ler_texto(mensagem, tamanho_maximo=50, obrigatorio=True):
    """Lê um texto, sem aceitar vazio (se obrigatório) nem acima do tamanho máximo."""
    while True:
        valor = input(mensagem).strip()
        if valor == "" and obrigatorio:
            print("  ⚠ Este campo não pode ficar em branco.")
            continue
        if len(valor) > tamanho_maximo:
            print(f"  ⚠ Use no máximo {tamanho_maximo} caracteres.")
            continue
        return valor


def ler_decimal(mensagem, minimo=0.0, maximo=None, permitir_zero=False):
    """Lê um número decimal (aceita vírgula ou ponto) dentro de uma faixa."""
    while True:
        texto = input(mensagem).strip().replace(",", ".")
        try:
            valor = float(texto)
        except ValueError:
            print("  ⚠ Valor inválido. Digite um número, por exemplo 12,5.")
            continue
        if valor != valor or valor in (float("inf"), float("-inf")):
            print("  ⚠ Valor inválido.")
            continue
        if valor == 0 and not permitir_zero:
            print("  ⚠ O valor precisa ser maior que zero.")
            continue
        if valor < minimo:
            if minimo == 0:
                print("  ⚠ O valor não pode ser negativo.")
            else:
                print(f"  ⚠ O valor não pode ser menor que {minimo:g}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"  ⚠ O valor não pode ser maior que {maximo}.")
            continue
        return round(valor, 2)


def ler_inteiro(mensagem, minimo=None, maximo=None):
    """Lê um número inteiro dentro de uma faixa."""
    while True:
        texto = input(mensagem).strip()
        if not texto.lstrip("-").isdigit():
            print("  ⚠ Digite um número inteiro.")
            continue
        valor = int(texto)
        if minimo is not None and valor < minimo:
            print(f"  ⚠ O valor deve ser maior ou igual a {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"  ⚠ O valor deve ser menor ou igual a {maximo}.")
            continue
        return valor


def ler_data(mensagem):
    """Lê uma data no formato dd/mm/aaaa, sem aceitar datas futuras."""
    while True:
        texto = input(mensagem).strip()
        try:
            data = datetime.strptime(texto, "%d/%m/%Y")
        except ValueError:
            print("  ⚠ Data inválida. Use o formato dd/mm/aaaa, por exemplo 15/08/2026.")
            continue
        if data > datetime.now():
            print("  ⚠ A data da colheita não pode estar no futuro.")
            continue
        if data.year < 2000:
            print("  ⚠ Informe uma data a partir de 2000.")
            continue
        return data.strftime("%d/%m/%Y")


def ler_opcao(titulo, opcoes):
    """Mostra uma tupla de opções numeradas e devolve a opção escolhida."""
    print(titulo)
    for numero, opcao in enumerate(opcoes, start=1):
        print(f"  {numero} - {opcao}")
    indice = ler_inteiro("Opção: ", 1, len(opcoes))
    return opcoes[indice - 1]


def confirmar(mensagem):
    """Pergunta S/N e devolve True ou False."""
    while True:
        resposta = input(f"{mensagem} (S/N): ").strip().upper()
        if resposta in ("S", "SIM"):
            return True
        if resposta in ("N", "NAO", "NÃO"):
            return False
        print("  ⚠ Responda S ou N.")
