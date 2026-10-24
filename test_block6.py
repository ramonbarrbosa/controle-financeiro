import os
import re
import sqlite3
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TABELAS_ESPERADAS = {'categorias', 'transacoes', 'investimentos', 'orcamentos', 'limites_categoria'}


def ler_arquivo(nome):
    with open(os.path.join(BASE_DIR, nome), encoding='utf-8') as f:
        return f.read()


def extrair_sql_funcao(nome_funcao):
    """Extrai os blocos db.run(`...`) de uma função do js/db.js (garante que o teste usa o schema real)."""
    js = ler_arquivo('js/db.js')
    inicio = js.index(f'function {nome_funcao}(')
    fim = js.index('\n}\n', inicio)
    return re.findall(r'db\.run\(`(.*?)`', js[inicio:fim], re.S)


def aplicar_sql_funcao(conn, nome_funcao):
    for bloco in extrair_sql_funcao(nome_funcao):
        conn.executescript(bloco)


def possui_cabecalho_sqlite(dados):
    # Espelha possuiCabecalhoSQLite() do js/db.js
    return dados[:16] == b'SQLite format 3\x00'


def validar_backup_fincontrol(conn):
    # Espelha a checagem de restaurarArquivoSQLite() do js/db.js
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('categorias', 'transacoes')"
    ).fetchall()
    return len(rows) == 2


def contar(conn, tabela):
    return conn.execute(f'SELECT COUNT(*) FROM {tabela}').fetchone()[0]


def test_exportar_e_restaurar_backup():
    conn = sqlite3.connect(':memory:')
    aplicar_sql_funcao(conn, 'criarEstruturaInicial')
    conn.executemany(
        "INSERT INTO categorias (nome, tipo) VALUES (?, ?)",
        [('Salário', 'Receita'), ('Alimentação', 'Despesa')]
    )
    conn.execute("INSERT INTO transacoes (tipo, valor, descricao, data_vencimento, categoria_id, status) "
                 "VALUES ('receita', 5000.0, 'Salário', '2026-10-05', 1, 'Recebido')")
    conn.execute("INSERT INTO transacoes (tipo, valor, descricao, data_vencimento, categoria_id) "
                 "VALUES ('despesa', 350.5, 'Mercado', '2026-10-12', 2)")
    conn.execute("INSERT INTO investimentos (nome, valor, tipo, data_aporte) VALUES ('CDB', 1000, 'Renda Fixa', '2026-10-01')")
    conn.execute("INSERT INTO orcamentos (ano_mes, limite_geral) VALUES ('2026-10', 4000)")
    conn.commit()

    with tempfile.TemporaryDirectory() as tmp:
        caminho = os.path.join(tmp, 'fincontrol_backup_2026-10-23.sqlite')
        destino = sqlite3.connect(caminho)
        conn.backup(destino)
        destino.close()

        with open(caminho, 'rb') as f:
            assert possui_cabecalho_sqlite(f.read())

        restaurado = sqlite3.connect(caminho)
        assert validar_backup_fincontrol(restaurado)
        for tabela in TABELAS_ESPERADAS:
            assert contar(restaurado, tabela) == contar(conn, tabela), tabela
        total = restaurado.execute("SELECT SUM(valor) FROM transacoes").fetchone()[0]
        assert total == 5350.5
        restaurado.close()
    print("[PASS] 1. Exportação e restauração preservam todas as tabelas e valores.")


def test_rejeita_arquivos_invalidos():
    assert not possui_cabecalho_sqlite(b'Isto nao e um banco de dados')
    assert not possui_cabecalho_sqlite(b'')

    # SQLite válido, mas que não é do FinControl
    outro = sqlite3.connect(':memory:')
    outro.execute('CREATE TABLE clientes (id INTEGER PRIMARY KEY)')
    assert not validar_backup_fincontrol(outro)

    # Só uma das tabelas obrigatórias
    parcial = sqlite3.connect(':memory:')
    parcial.execute('CREATE TABLE categorias (id INTEGER PRIMARY KEY)')
    assert not validar_backup_fincontrol(parcial)
    print("[PASS] 2. Arquivos inválidos ou de outro sistema são rejeitados.")


def test_migracoes_em_backup_antigo():
    # Backup de uma versão antiga: só categorias e transações
    conn = sqlite3.connect(':memory:')
    conn.executescript("""
        CREATE TABLE categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, tipo TEXT NOT NULL);
        CREATE TABLE transacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL, valor REAL NOT NULL);
        INSERT INTO categorias (nome, tipo) VALUES ('Investimentos', 'Receita');
    """)
    assert validar_backup_fincontrol(conn)

    aplicar_sql_funcao(conn, 'garantirMigracoes')
    aplicar_sql_funcao(conn, 'garantirMigracoes')  # idempotente

    tabelas = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert TABELAS_ESPERADAS <= tabelas
    nome = conn.execute("SELECT nome FROM categorias WHERE id = 1").fetchone()[0]
    assert nome == 'Investimento (Patrimônio)'
    print("[PASS] 3. Migrações atualizam backups antigos de forma idempotente.")


def test_modal_backup_possui_handlers():
    html = ler_arquivo('index.html')
    inicio = html.index('id="modal-backup"')
    fim = html.index('<!-- Scripts da Aplicação -->', inicio)
    chamadas = set(re.findall(r'on(?:click|change)="(\w+)\(', html[inicio:fim]))
    chamadas.add('abrirModalBackup')
    faltando = [fn for fn in chamadas if not re.search(rf'function {fn}\(', html)]
    assert not faltando, f'Funções não implementadas: {faltando}'

    db_js = ler_arquivo('js/db.js')
    for fn in ('exportarArquivoSQLite', 'restaurarArquivoSQLite', 'obterEstatisticasBanco', 'possuiCabecalhoSQLite'):
        assert f'function {fn}(' in db_js, fn
    assert '\x00' not in db_js
    print("[PASS] 4. Todos os botões do modal de Backup possuem funções implementadas.")


def test_service_worker_cache():
    sw = ler_arquivo('sw.js')
    html = ler_arquivo('index.html')
    # Todo script/stylesheet externo do index.html deve estar na lista de cache do SW
    # (imagens decorativas ficam a cargo do cache dinâmico)
    externos = re.findall(r'<(?:script|link)[^>]*(?:src|href)="(https://[^"]+)"', html)
    faltando = [url for url in externos if url not in sw]
    assert not faltando, f'URLs externas fora do cache offline: {faltando}'
    assert 'cdn.jsdelivr.net/npm/chart.js"' not in html, 'Chart.js deve ter versão fixa'
    print("[PASS] 5. Service Worker cobre todos os recursos externos para uso offline.")


if __name__ == '__main__':
    test_exportar_e_restaurar_backup()
    test_rejeita_arquivos_invalidos()
    test_migracoes_em_backup_antigo()
    test_modal_backup_possui_handlers()
    test_service_worker_cache()
    print("\nTODOS OS TESTES DO BLOCO 6 (RF-04 BACKUP E PWA) PASSARAM! [100%]")
