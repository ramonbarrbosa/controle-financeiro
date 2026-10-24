# Documentação do Projeto: Aplicativo de Controle Financeiro

## 1. Visão Geral do Projeto
O objetivo deste projeto é desenvolver uma aplicativo mobile (Android), leve e intuitiva para gestão financeira pessoal/familiar. O sistema permitirá o registro de receitas e despesas (lançamentos), categorização, visualização de relatórios mensais e geração de backups de dados em formato local (SQLite).
O aplicativo em questão terá que ser escalável, pois há grandes possibilidades de ter futuras melhorias.

# 2. Requisitos Funcionais (RF)

## RF-01: Gestão de Categorias
- O sistema deve permitir cadastrar, listar, editar e remover categorias.
- Cada categoria deve ter um nome e um tipo (Receita ou Despesa).
- Exemplo de categorias padrão: Alimentação, Lazer, Saúde, Transporte, Salário, Investimentos.

## RF-02: Gestão de Transações (Receitas e Despesas)
O sistema deve permitir o cadastro de transações financeiras.

Campos obrigatórios: 
- Tipo (Receita ou Despesa)
- Valor (R$)
- Descrição
- Data de Vencimento
- Categoria (vínculo com RF-01) 

Campos complementares (Opcionais):
- Status (Pago, Pendente, Recebido)
- Data de Pagamento/Efetivação
- Observações/Notas adicionais

## RF-03: Análise e Relatório Mensal

Exibição do resumo do mês selecionado (Mês/Ano):

- Total de Receitas
- Total de Despesas
- Saldo do Mês (Receitas - Despesas)

Consolidação de gastos agrupados por Categoria com percentual de representatividade.
Destaque para contas pendentes vs. contas pagas no mês.

## RF-04: Gestão de Backup e Dados

- Funcionalidade para exportar/copiar o arquivo do banco de dados SQLite (.db / .sqlite).
- Opção de restauração de banco a partir de um arquivo de backup.

# 3. Requisitos Não Funcionais (RNF)

## RNF-01: Armazenamento Leve

- Utilização do banco de dados relacional SQLite, garantindo portabilidade e baixo consumo de recursos sem necessidade de um servidor de banco dedicado.

## RNF-02: Usabilidade

- Interface limpa, intuitiva e responsiva para rápida inserção de dados diários.

## RNF-03: Segurança dos Dados

- Dados mantidos de forma local, garantindo privacidade ao usuário.

## Observações:
- Todo o código desse aplicativo será armazenando no github;
- Execução no celular android via Github Page apenas instalando via navegador;
- Já criei uma .venv (Ambiente virtual)
- AS bibliotecas que serão utilizadas neste projeto devem ser salvas no arquivo "requetiments.txt" para caso mais na frente seja necessário chamar novos profisionais para colaborar com o projeto.
- Dividir os blocos de desenvolvimento e a cada conclusão, testar antes de avançar par o próximo.
- Linguagens de programação que possam ser utilizadas no desenvolvimento (Python - HTML - CSS - JavaScript).