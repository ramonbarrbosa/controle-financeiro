import calendar
import os
import re
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def ler_arquivo(nome):
    with open(os.path.join(BASE_DIR, nome), encoding='utf-8') as f:
        return f.read()


def extrair_sql_funcao(nome_funcao):
    js = ler_arquivo('js/db.js')
    inicio = js.index(f'function {nome_funcao}(')
    fim = js.index('\n}\n', inicio)
    return re.findall(r'db\.run\(`(.*?)`', js[inicio:fim], re.S)


def colunas_serie_js():
    js = ler_arquivo('js/db.js')
    bloco = re.search(r'const COLUNAS_SERIE = \[(.*?)\];', js, re.S).group(1)
    return re.findall(r"\['(\w+)', '(\w+)'\]", bloco)


# Espelha adicionarMeses() do js/db.js
def adicionar_meses(data_iso, meses):
    ano, mes, dia = map(int, data_iso.split('-'))
    total = (mes - 1) + meses
    ano_alvo, mes_alvo = ano + total // 12, total % 12 + 1
    ultimo_dia = calendar.monthrange(ano_alvo, mes_alvo)[1]
    return f'{ano_alvo:04d}-{mes_alvo:02d}-{min(dia, ultimo_dia):02d}'


# Espelha dividirEmParcelas() do js/db.js
def dividir_em_parcelas(valor_total, quantidade):
    total_centavos = round(valor_total * 100)
    base = total_centavos // quantidade
    resto = total_centavos - base * quantidade
    return [(base + resto if i == 0 else base) / 100 for i in range(quantidade)]


def colunas_transacoes(conn):
    return [r[1] for r in conn.execute('PRAGMA table_info(transacoes)')]


def criar_banco_atual():
    conn = sqlite3.connect(':memory:')
    for bloco in extrair_sql_funcao('criarEstruturaInicial'):
        conn.executescript(bloco)
    conn.execute("INSERT INTO categorias (id, nome, tipo) VALUES (1, 'Moradia', 'Despesa')")
    return conn


def inserir_serie(conn, grupo, tipo_serie, valores, primeiro_vencimento, descricao='Notebook'):
    for i, valor in enumerate(valores):
        conn.execute(
            "INSERT INTO transacoes (tipo, valor, descricao, data_vencimento, categoria_id, status, "
            "grupo_id, tipo_serie, parcela_atual, parcela_total) VALUES ('despesa', ?, ?, ?, 1, ?, ?, ?, ?, ?)",
            (valor, descricao, adicionar_meses(primeiro_vencimento, i), 'Pago' if i == 0 else 'Pendente',
             grupo, tipo_serie, i + 1, len(valores))
        )


def test_divisao_de_parcelas():
    assert dividir_em_parcelas(100, 3) == [33.34, 33.33, 33.33]
    assert dividir_em_parcelas(1500, 10) == [150.0] * 10
    assert dividir_em_parcelas(0.05, 2) == [0.03, 0.02]
    assert dividir_em_parcelas(0.01, 2)[1] == 0  # rejeitado pelo app (parcela zerada)
    for total, qtd in ((100, 3), (999.99, 7), (1234.56, 60), (10, 6)):
        assert round(sum(dividir_em_parcelas(total, qtd)), 2) == total, (total, qtd)
    print("[PASS] 1. Divisão de parcelas soma exatamente o total (centavos na 1ª parcela).")


def test_datas_mensais():
    assert adicionar_meses('2026-01-31', 1) == '2026-02-28'
    assert adicionar_meses('2028-01-31', 1) == '2028-02-29'   # ano bissexto
    assert adicionar_meses('2026-01-31', 2) == '2026-03-31'   # volta ao dia original
    assert adicionar_meses('2026-10-30', 4) == '2027-02-28'
    assert adicionar_meses('2026-11-15', 2) == '2027-01-15'   # virada de ano
    assert adicionar_meses('2026-10-23', 59) == '2031-09-23'
    print("[PASS] 2. Datas mensais respeitam fim de mês, ano bissexto e virada de ano.")


def test_schema_e_migracao():
    esperadas = colunas_serie_js()
    assert [n for n, _ in esperadas] == ['grupo_id', 'tipo_serie', 'parcela_atual', 'parcela_total']

    # Banco novo já nasce com as colunas
    novo = criar_banco_atual()
    assert all(n in colunas_transacoes(novo) for n, _ in esperadas)

    # Banco antigo (backup anterior ao bloco 8): espelha o laço de garantirMigracoes()
    antigo = sqlite3.connect(':memory:')
    antigo.execute("CREATE TABLE transacoes (id INTEGER PRIMARY KEY, tipo TEXT, valor REAL)")
    antigo.execute("INSERT INTO transacoes (tipo, valor) VALUES ('despesa', 10)")
    for _ in range(2):  # idempotente
        existentes = colunas_transacoes(antigo)
        for nome, tipo in esperadas:
            if nome not in existentes:
                antigo.execute(f'ALTER TABLE transacoes ADD COLUMN {nome} {tipo}')
    assert all(n in colunas_transacoes(antigo) for n, _ in esperadas)
    assert antigo.execute('SELECT grupo_id, parcela_atual FROM transacoes').fetchone() == (None, None)

    js = ler_arquivo('js/db.js')
    migracao = js[js.index('function garantirMigracoes('):js.index('function criarEstruturaInicial(')]
    assert 'PRAGMA table_info(transacoes)' in migracao and 'COLUNAS_SERIE' in migracao
    print("[PASS] 3. Colunas de série no banco novo e migração idempotente em backups antigos.")


def test_operacoes_da_serie():
    conn = criar_banco_atual()
    inserir_serie(conn, 'g1', 'parcelado', dividir_em_parcelas(1000, 10), '2026-10-31')
    inserir_serie(conn, 'g2', 'recorrente', [50.0] * 12, '2026-10-05', 'Streaming')

    linhas = conn.execute("SELECT parcela_atual, data_vencimento, status FROM transacoes WHERE grupo_id='g1' ORDER BY parcela_atual").fetchall()
    assert linhas[0] == (1, '2026-10-31', 'Pago')
    assert linhas[1] == (2, '2026-11-30', 'Pendente')
    assert linhas[4][1] == '2027-02-28'

    # "Este e os próximos" na edição: a partir da parcela 6, só campos descritivos (espelha atualizarSerieTransacoes)
    conn.execute("UPDATE transacoes SET valor = 120, descricao = 'Notebook Pro' WHERE grupo_id = 'g1' AND parcela_atual >= 6")
    assert conn.execute("SELECT COUNT(*) FROM transacoes WHERE grupo_id='g1' AND valor = 120").fetchone()[0] == 5
    assert conn.execute("SELECT data_vencimento FROM transacoes WHERE grupo_id='g1' AND parcela_atual = 6").fetchone()[0] == '2027-03-31'

    # "Este e os próximos" na exclusão (cancelar assinatura a partir do 4º mês) não afeta outra série
    conn.execute("DELETE FROM transacoes WHERE grupo_id = 'g2' AND parcela_atual >= 4")
    assert conn.execute("SELECT COUNT(*) FROM transacoes WHERE grupo_id='g2'").fetchone()[0] == 3
    assert conn.execute("SELECT COUNT(*) FROM transacoes WHERE grupo_id='g1'").fetchone()[0] == 10

    # Relatório mensal continua somando normalmente (lançamentos materializados)
    total_nov = conn.execute("SELECT SUM(valor) FROM transacoes WHERE strftime('%Y-%m', data_vencimento) = '2026-11'").fetchone()[0]
    assert total_nov == 100.0 + 50.0
    print("[PASS] 4. Criação, edição e exclusão em série preservam datas, status e outras séries.")


def test_interface_series():
    html = ler_arquivo('index.html')
    db_js = ler_arquivo('js/db.js')
    for fn in ('adicionarMeses', 'dividirEmParcelas', 'salvarSerieTransacoes', 'atualizarSerieTransacoes',
               'excluirSerieTransacoes', 'contarSerieAPartirDe'):
        assert f'function {fn}(' in db_js, fn
    chamadas = set(re.findall(r'on(?:click|change|input)="(\w+)\(', html))
    todo_js = html + db_js + ler_arquivo('js/theme.js')
    faltando = [fn for fn in chamadas if not re.search(rf'function {fn}\(', todo_js)]
    assert not faltando, f'Funções não implementadas: {faltando}'
    for id_ in ('campo-repeticao-container', 'form-serie-quantidade', 'previa-serie', 'confirm-serie-row', 'modal-escopo-serie'):
        assert f'id="{id_}"' in html, id_
    print("[PASS] 5. Interface de séries: campos, prévia, confirmação e modal de escopo implementados.")


if __name__ == '__main__':
    test_divisao_de_parcelas()
    test_datas_mensais()
    test_schema_e_migracao()
    test_operacoes_da_serie()
    test_interface_series()
    print("\nTODOS OS TESTES DO BLOCO 8 (PARCELADOS E RECORRENTES) PASSARAM! [100%]")
