# FIAP - Faculdade de Informática e Administração Paulista

# FarmTech Solutions – Monitor de Perdas na Colheita de Cana-de-Açúcar

## 👨‍🎓 Integrantes
- Tárcio Barros – RM576489

## 👩‍🏫 Professores
### Tutor(a)
- Sabrina Otoni
### Coordenador(a)
- André Godoi

---

## 📜 Descrição

### A dor do agronegócio que estamos tratando

O Brasil é o maior produtor mundial de cana-de-açúcar, com safras na casa de
**620 milhões de toneladas**. Mesmo assim, as **perdas durante a colheita** ainda
são muito altas. Segundo a SOCICANA, na colheita **mecanizada a perda chega a
15%** da produção, enquanto na **colheita manual raramente passa de 5%**.

Só no estado de São Paulo, com cerca de 3 milhões de hectares plantados e
produtividade próxima de 100 t/ha, essas perdas representam um prejuízo de
**R$ 20 milhões por ano** para o setor.

O problema é que, na maioria das fazendas, a perda **não é medida de forma
sistemática**. O produtor percebe que colheu menos, mas não sabe em quais
talhões, em que tipo de colheita nem quanto isso custou em reais. Por isso, não
sabe onde agir primeiro.

### A solução

O **Monitor de Perdas na Colheita** é uma aplicação de terminal em Python que:

1. **Cadastra os talhões** de cana (área, variedade e produtividade esperada);
2. **Registra cada colheita** (data, tipo manual ou mecanizada, toneladas colhidas e preço da tonelada);
3. **Calcula automaticamente** a perda em toneladas, em % e em **reais**;
4. **Classifica** a colheita como **ACEITÁVEL** (até 5%), **ATENÇÃO** (até 10%) ou **CRÍTICA** (acima de 10%) e compara com a referência do tipo de colheita;
5. **Sugere ações** de correção específicas para o tipo de colheita (ex.: regulagem do corte de base, velocidade da colhedora, sincronismo com o transbordo);
6. Gera um **painel gerencial** com comparativo manual × mecanizada, ranking dos maiores prejuízos, plano de ação e a **economia possível** se a perda cair para a meta de 5%;
7. Grava tudo no **Oracle**, mantém **backup em JSON** e registra cada operação em um **log de texto**.

### Inovação

- **A perda é traduzida em dinheiro**, com a economia possível ao atingir a meta. Isso ajuda o produtor a decidir onde investir em ajuste ou treinamento.
- **Diagnóstico com recomendação automática**: o sistema não só aponta o problema, mas indica o que verificar no campo conforme o tipo de colheita.
- **Funcionamento online e offline**: sem conexão com o Oracle (comum no campo), o sistema continua funcionando com o arquivo JSON, que pode ser importado no banco depois.

---

## ✅ Conteúdos da disciplina aplicados

| Conteúdo | Onde está no código |
|---|---|
| **Funções** (com retorno e parâmetros) | `calculos.py`: `calcular_perda()`, `classificar_perda()`, `calcular_prejuizo()`, `calcular_economia_potencial()`; `validacao.py`: `ler_decimal()`, `ler_data()` etc. |
| **Procedimentos** (sem retorno, com parâmetros) | `arquivos.registrar_log()`, `arquivos.salvar_relatorio_txt()`, `main.exibir_diagnostico()`, `main.imprimir_tabela()` |
| **Lista** | `talhoes` e `colheitas` em `main.py` (listas de registros) |
| **Tupla** | `TIPOS_COLHEITA`, `FAIXAS_PERDA` (`constantes.py`), `OPCOES_MENU` e a tupla de lançamentos de exemplo; `calcular_perda()` devolve uma tupla |
| **Dicionário** | Cada talhão e colheita é um dicionário; `REFERENCIA_PERDA` e `RECOMENDACOES` são dicionários de consulta; o menu usa um dicionário de despacho |
| **Tabela de memória** | `montar_tabela_colheitas()` converte os registros em uma lista de listas, usada para exibir, ordenar o ranking e gerar o relatório |
| **Arquivo texto** | `logs/operacoes.log` (histórico de operações) e `dados/relatorio_perdas.txt` (relatório) |
| **Arquivo JSON** | `dados/colheitas.json`: backup automático, exportação e importação com validação |
| **Banco de dados Oracle** | `banco.py`: conexão com `oracledb`, criação das tabelas, INSERT, SELECT, UPDATE, DELETE e transação com commit/rollback |
| **Validação de entrada** | `validacao.py`: números (aceita vírgula), faixas mínimas e máximas, data válida e não futura, textos não vazios e com tamanho limitado, opções e confirmação S/N |

---

## 📁 Estrutura de pastas

- **assets/**: imagens e arquivos não estruturados.
- **config/**: `config_oracle.exemplo.json`, um modelo de configuração do banco. Copie para `config_oracle.json` e preencha com o seu usuário (esse arquivo fica fora do Git).
- **document/**: documentos do projeto.
- **scripts/**: `criar_tabelas.sql`, com a criação das tabelas e uma consulta de apoio, e `testar_oracle.py`, o teste automático de integração com o Oracle (`python scripts/testar_oracle.py`).
- **src/**: código-fonte.
  - `main.py`: menu e fluxo da aplicação
  - `calculos.py`: regras de negócio (perdas, classificação, recomendações)
  - `validacao.py`: entrada de dados com validação
  - `arquivos.py`: leitura e gravação de JSON e texto
  - `banco.py`: conexão e operações no Oracle
  - `constantes.py`: tuplas e dicionários de referência
- **README.md**: este guia.

Pastas geradas durante a execução: `dados/` (JSON e relatório) e `logs/` (log de operações).

---

## 🔧 Como executar o código

**Pré-requisitos:** Python 3.9 ou superior e acesso a um banco Oracle (opcional).

```bash
# 1. Instalar a biblioteca do Oracle
pip install -r requirements.txt

# 2. (Opcional) Configurar o acesso ao banco
#    copie config/config_oracle.exemplo.json para config/config_oracle.json
#    e preencha usuário e senha. Se não fizer isso, o programa pergunta na hora.

# 3. Executar
python src/main.py
```

Ao iniciar, o sistema pergunta se deve conectar ao Oracle:
- **S**: conecta, cria as tabelas `FT_TALHAO` e `FT_COLHEITA` (se ainda não existirem) e carrega os dados do banco;
- **N**: trabalha em modo offline, com os dados do arquivo JSON.

Para uma demonstração rápida, use a opção **14 – Carregar dados de exemplo** e depois a opção **9 – Painel de perdas**.

### Exemplo do painel

```
 RESUMO GERAL
   Colheitas analisadas ........: 6
   Produção esperada ...........: 24.050,00 t
   Cana perdida no campo .......: 1.840,00 t (7,65%)
   Prejuízo total estimado .....: R$ 278.875,00
   Economia se perda ≤ 5% ......: R$ 105.773,45

 COMPARATIVO MANUAL x MECANIZADA
   Tipo       | Colheitas | Perda (t) | Perda média | Prejuízo
   -----------+-----------+-----------+-------------+--------------
   Manual     |         2 |    160,00 |       3,56% |  R$ 24.000,00
   Mecanizada |         4 |  1.680,00 |       8,59% | R$ 254.875,00
```

> Os dados de exemplo são fictícios e servem só para demonstração.

### Teste de integração com o Oracle

O script `scripts/testar_oracle.py` executa no banco cada operação usada pelo
sistema e confere o resultado. Ele usa IDs a partir de 900000 e apaga os
registros de teste ao final.

```bash
python scripts/testar_oracle.py
```

Resultado no Oracle da FIAP (`oracle.fiap.com.br:1521/ORCL`): **11 de 11 testes OK**.
Foram verificados conexão e criação das tabelas, INSERT, SELECT e UPDATE de
talhão e colheita (com datas e acentos), a restrição CHECK do tipo de colheita,
o cálculo do próximo ID pelo banco, o DELETE e a exclusão em cascata
(`ON DELETE CASCADE`).

---

## 📚 Referências

- CHB Agro. *Perdas na colheita de cana: você sabe como reduzi-las?* https://blog.chbagro.com.br/perdas-na-colheita-de-cana-voce-sabe-como-reduzi-las
- Unicesumar – EPCC 2009. Artigo sobre perdas na colheita de cana-de-açúcar. https://www.unicesumar.edu.br/epcc-2009/wp-content/uploads/sites/77/2016/07/jefferson_vieira_jose3.pdf
- AEVO. *Agrotech*. https://blog.aevo.com.br/agrotech/

## 🗃 Histórico de lançamentos

* 0.2.0 - 13/10/2026
    * Nova versão focada em perdas na colheita da cana: funções, estruturas de dados, arquivos texto/JSON e Oracle
* 0.1.0
    * Primeira versão FarmTech: cálculo de área de plantio e insumos (café e cana)

## 📋 Licença

Projeto acadêmico desenvolvido para a FIAP, sob a licença [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/).
