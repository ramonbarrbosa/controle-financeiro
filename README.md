# FINControl – Controle Financeiro Pessoal

Aplicativo leve para organizar receitas e despesas pessoais ou familiares. Funciona direto no navegador,
pode ser instalado no celular Android como um app (PWA) e **guarda todos os dados apenas no próprio aparelho**:
não há servidor, login nem envio de informações para a internet.

**Acesse:** [https://ramonbarrbosa.github.io/controle-financeiro/](https://ramonbarrbosa.github.io/controle-financeiro/)

---

## 1. Como usar o aplicativo

### Instalação no celular
1. Abra [ramonbarrbosa.github.io/controle-financeiro](https://ramonbarrbosa.github.io/controle-financeiro/) no Chrome do Android.
2. No menu do navegador, toque em **Instalar app** (ou **Adicionar à tela inicial**).
3. O FINControl passa a abrir como um aplicativo comum e funciona **mesmo sem internet**.

> Os dados ficam no navegador do aparelho. Cada celular/navegador tem os seus próprios dados;
> para levá-los a outro aparelho, use o **Backup** e a **Restauração**.

### Telas principais
O app tem três abas no topo:

| Aba | Para que serve |
|---|---|
| **Dashboard** | Visão geral do mês: saldo, contas pagas x pendentes, gráficos, investimentos e teto de gastos. |
| **Extrato** | Lista de todos os lançamentos do mês, com busca e filtros. |
| **Confirmação** | Revisão do lançamento antes de gravar (deslize para confirmar). |

No topo também ficam os botões de **tema claro/escuro**, **ocultar valores** (olho, útil em público)
e **novo lançamento** (+).

### Lançar uma receita ou despesa
1. Toque em **+**, **Receita** ou **Despesa**.
2. Preencha valor, vencimento, descrição e categoria. Status, data de pagamento, conta/cartão e observações são opcionais.
3. Escolha a **repetição**:
   - **Única**: um lançamento só.
   - **Parcelada**: informe o **valor total** e o **nº de parcelas** (2 a 60). O app divide o valor e cria uma parcela por mês.
     Ex.: R$ 100,00 em 3x → R$ 33,34 + R$ 33,33 + R$ 33,33.
   - **Recorrente**: informe o **valor mensal** e **por quantos meses** ele se repete (padrão 12). Ex.: aluguel, assinaturas.
4. Toque em **Revisar e Confirmar**, confira os dados e **deslize para confirmar**.

Lançamentos parcelados e recorrentes mostram um selo com a posição na série (ex.: **3/10**).
Ao editar ou excluir um deles, o app pergunta se a ação vale para **somente este** ou para **este e os próximos**.

### Marcar como pago
No Extrato, toque no selo **Pendente** de um lançamento para marcá-lo como **Pago/Recebido** (e toque de novo para desfazer).

### Outras funções
| Função | Onde fica | O que faz |
|---|---|---|
| **Categorias** | Dashboard → Categorias, ou botão **+** ao lado do campo Categoria no lançamento | Criar, renomear e remover categorias de receita e despesa, com ícone e cor. |
| **Relatório mensal** | Dashboard → Relatório | Totais do mês, saldo, % de cada categoria nas despesas e contas pagas x pendentes. Pode ser impresso ou salvo em PDF. |
| **Investimentos** | Dashboard → card Investimentos | Registro do patrimônio investido (Renda Fixa, Renda Variável, Fundos, Outros). |
| **Teto de gastos** | Dashboard → card Teto de Gastos | Define um limite de despesas para o mês e mostra quanto já foi usado. |
| **Backup** | Dashboard → Backup | Baixa uma cópia completa dos dados (arquivo `.sqlite`) e restaura a partir de um backup. |

### Backup: proteja seus dados
Como os dados ficam só no aparelho, **limpar os dados do navegador ou trocar de celular apaga tudo** se não houver backup.
- Em **Backup → Baixar Arquivo de Backup**, guarde o arquivo em local seguro (Google Drive, e-mail, computador).
- Para recuperar, use **Backup → Restaurar de Arquivo** e selecione o `.sqlite` (ou `.db`). A restauração **substitui todos os dados atuais**.
- O app mostra um **lembrete no Dashboard** quando o último backup passa do prazo escolhido (7, 15 ou 30 dias; padrão 7).
  O lembrete pode ser adiado com **Lembrar amanhã** ou desativado no próprio modal de Backup.

---

## 2. Documentação técnica

### Visão geral
- **Tipo:** Progressive Web App (PWA) 100% client-side, publicado no GitHub Pages.
- **Banco de dados:** SQLite rodando no navegador via WebAssembly ([sql.js](https://sql.js.org)).
  O arquivo do banco é persistido no **IndexedDB** a cada alteração.
- **Interface:** HTML + JavaScript puro, Tailwind CSS (compilado localmente), Chart.js, Font Awesome e fonte Inter.
- **Offline:** Service Worker com estratégia *network first* e cache de todos os arquivos locais e bibliotecas externas.
- **Python:** usado apenas como ferramenta de desenvolvimento (testes automatizados e build do CSS); não faz parte do app publicado.

### Estrutura de arquivos
```
index.html            Interface completa do app (telas, modais e lógica de interface)
js/db.js              Camada de dados: SQLite, migrações, CRUD, séries, relatórios e backup
js/theme.js           Tema claro/escuro
css/input.css         Entrada do Tailwind
css/tailwind.css      CSS gerado (versionado; não editar à mão)
tailwind.config.js    Cores e fonte do tema
sw.js                 Service Worker (cache offline)
manifest.json         Manifesto do PWA (nome, ícone, cores)
assets/icon.svg       Ícone do app
build_css.py          Gera css/tailwind.css com o Tailwind Standalone CLI
test_block*.py        Testes automatizados de cada bloco de desenvolvimento
Especificacao.md      Requisitos do projeto (RF/RNF)
model_interface.html  Modelo visual de referência da interface
requirements.txt      Dependências de desenvolvimento
```

### Modelo de dados (SQLite)
| Tabela | Conteúdo |
|---|---|
| `categorias` | Nome, tipo (Receita/Despesa), ícone e cor. |
| `transacoes` | Tipo, valor, descrição, vencimento, categoria, status (Pendente/Pago/Recebido), data de pagamento, conta, observações e dados de série (`grupo_id`, `tipo_serie`, `parcela_atual`, `parcela_total`). |
| `investimentos` | Nome, valor, tipo e data do aporte. |
| `orcamentos` | Teto de gastos por mês (`ano_mes`). |
| `limites_categoria` | Teto por categoria e mês. |

- **Migrações:** `garantirMigracoes()` em `js/db.js` atualiza bancos antigos automaticamente ao abrir o app
  ou restaurar um backup (novas tabelas e colunas são adicionadas sem perder dados).
- **Séries:** parcelados e recorrentes são gravados como lançamentos individuais ligados pelo `grupo_id`.
  Assim, relatórios, gráficos, teto e saldo funcionam sem tratamento especial.

### Requisitos atendidos (ver `Especificacao.md`)
| Requisito | Implementação |
|---|---|
| RF-01 Categorias | Cadastro, edição e remoção; categorias padrão criadas na primeira execução. |
| RF-02 Transações | Campos obrigatórios e opcionais; lançamentos únicos, parcelados e recorrentes. |
| RF-03 Relatório mensal | Receitas, despesas, saldo, % por categoria, pagas x pendentes. |
| RF-04 Backup | Exportação e restauração do arquivo SQLite, com validação e lembrete periódico. |
| RNF-01 a 03 | SQLite local, interface responsiva e dados exclusivamente no aparelho. |

### Ambiente de desenvolvimento
Pré-requisitos: Python 3 (com a `.venv` do projeto) e um navegador.

```bash
# Instalar as dependências de desenvolvimento (uma vez, com a .venv ativada)
pip install -r requirements.txt

# Rodar o app localmente (abra http://localhost:8000)
python -m http.server 8000

# Gerar o CSS após alterar classes no index.html ou em js/
python build_css.py          # gera css/tailwind.css (minificado)
python build_css.py --watch  # regera automaticamente durante o desenvolvimento

# Executar os testes (um bloco por vez)
python test_block8.py
# ou todos de uma vez
pytest
```

- Na primeira execução, `build_css.py` baixa o Tailwind CSS Standalone CLI (v3.4.17) para `tools/`
  (pasta ignorada pelo Git; não requer Node.js).
- O Service Worker exige `http://localhost` ou `https://`; abrir o `index.html` direto pelo arquivo não ativa o modo offline.

### Regras do projeto
- **Sempre** rode `python build_css.py` e inclua `css/tailwind.css` no commit quando alterar classes do Tailwind
  (o `test_block7.py` acusa CSS desatualizado).
- Ao alterar arquivos cacheados ou a lista de arquivos do app, incremente `CACHE_NAME` em `sw.js`.
- Mudanças no banco devem entrar em `garantirMigracoes()` para manter compatibilidade com backups antigos.
- O desenvolvimento é feito em blocos, com testes ao fim de cada um antes de avançar.

### Histórico de blocos
| Bloco | Entrega |
|---|---|
| 1–2 | SQLite + IndexedDB, tema, categorias, investimentos e teto de gastos |
| 3–4 | Motor de transações (RF-02), extrato com filtros e ações rápidas |
| 5 | Relatório mensal (RF-03) e destaque de pagas x pendentes |
| 6 | Backup e restauração (RF-04) e cache offline do PWA |
| 7 | Tailwind CSS local (remoção do CDN) |
| 8 | Lançamentos parcelados e recorrentes |
| 9 | Lembrete de backup |
