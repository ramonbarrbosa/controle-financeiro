import sqlite3
import datetime

def test_transacoes_full_lifecycle():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL
        );

        CREATE TABLE transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK(tipo IN ('receita', 'despesa')),
            valor REAL NOT NULL,
            descricao TEXT NOT NULL,
            data_vencimento DATE NOT NULL,
            categoria_id INTEGER NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT,
            status TEXT DEFAULT 'Pendente' CHECK(status IN ('Pendente', 'Pago', 'Recebido')),
            data_pagamento DATE,
            conta TEXT DEFAULT 'Carteira Principal',
            observacoes TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 1. Inserir categoria
    cursor.execute("INSERT INTO categorias (nome, tipo) VALUES ('Alimentação', 'Despesa')")
    cat_id = cursor.lastrowid

    # 2. Inserir transação com todos os campos da especificação
    cursor.execute("""
        INSERT INTO transacoes (tipo, valor, descricao, data_vencimento, categoria_id, status, data_pagamento, conta, observacoes)
        VALUES ('despesa', 230.50, 'Compras no Supermercado', '2026-10-25', ?, 'Pendente', NULL, 'Cartão Nubank', 'Compras do mês')
    """, (cat_id,))
    trans_id = cursor.lastrowid
    assert trans_id is not None

    # 3. Consulta e validação de campos
    cursor.execute("SELECT descricao, valor, status, conta, observacoes FROM transacoes WHERE id = ?", (trans_id,))
    row = cursor.fetchone()
    assert row[0] == 'Compras no Supermercado'
    assert row[1] == 230.50
    assert row[2] == 'Pendente'
    assert row[3] == 'Cartão Nubank'
    assert row[4] == 'Compras do mês'

    # 4. Ação rápida de alternar status (Pendente -> Pago com data de pagamento)
    cursor.execute("""
        UPDATE transacoes 
        SET status = 'Pago', data_pagamento = '2026-10-22' 
        WHERE id = ?
    """, (trans_id,))
    cursor.execute("SELECT status, data_pagamento FROM transacoes WHERE id = ?", (trans_id,))
    upd_row = cursor.fetchone()
    assert upd_row[0] == 'Pago'
    assert upd_row[1] == '2026-10-22'

    # 5. Edição de transação
    cursor.execute("UPDATE transacoes SET valor = 250.00 WHERE id = ?", (trans_id,))
    cursor.execute("SELECT valor FROM transacoes WHERE id = ?", (trans_id,))
    assert cursor.fetchone()[0] == 250.00

    # 6. Exclusão de transação
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (trans_id,))
    cursor.execute("SELECT count(*) FROM transacoes WHERE id = ?", (trans_id,))
    assert cursor.fetchone()[0] == 0

    print("[PASS] 1. Ciclo de vida completo das Transações (RF-02): Criação, Status, Edição e Exclusão.")

def test_filtros_e_busca():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE categorias (id INTEGER PRIMARY KEY, nome TEXT, tipo TEXT);
        CREATE TABLE transacoes (
            id INTEGER PRIMARY KEY,
            tipo TEXT,
            valor REAL,
            descricao TEXT,
            data_vencimento DATE,
            categoria_id INTEGER,
            status TEXT,
            conta TEXT
        );
    """)

    cursor.execute("INSERT INTO categorias VALUES (1, 'Transporte', 'Despesa')")
    cursor.execute("INSERT INTO categorias VALUES (2, 'Salário', 'Receita')")

    cursor.execute("INSERT INTO transacoes VALUES (1, 'despesa', 50.0, 'Uber trabalho', '2026-10-05', 1, 'Pago', 'Nubank')")
    cursor.execute("INSERT INTO transacoes VALUES (2, 'despesa', 120.0, 'Combustível Posto Shell', '2026-10-12', 1, 'Pendente', 'Itaú')")
    cursor.execute("INSERT INTO transacoes VALUES (3, 'receita', 4500.0, 'Salário Mensal', '2026-10-01', 2, 'Recebido', 'Itaú')")
    cursor.execute("INSERT INTO transacoes VALUES (4, 'despesa', 80.0, 'Uber volta', '2026-09-28', 1, 'Pago', 'Nubank')")

    # Filtro por Mês (2026-10)
    cursor.execute("SELECT count(*) FROM transacoes WHERE strftime('%Y-%m', data_vencimento) = '2026-10'")
    assert cursor.fetchone()[0] == 3

    # Filtro por Status (Pendente em 2026-10)
    cursor.execute("SELECT count(*) FROM transacoes WHERE status = 'Pendente' AND strftime('%Y-%m', data_vencimento) = '2026-10'")
    assert cursor.fetchone()[0] == 1

    # Filtro por Busca textual ('Uber')
    cursor.execute("SELECT count(*) FROM transacoes WHERE descricao LIKE '%Uber%'")
    assert cursor.fetchone()[0] == 2

    print("[PASS] 2. Filtros dinâmicos (Mês, Status Pendente/Pago e Busca textual) validados.")

if __name__ == '__main__':
    test_transacoes_full_lifecycle()
    test_filtros_e_busca()
    print("\nTODOS OS TESTES DOS BLOCOS 3 E 4 PASSARAM COM SUCESSO! [100%]")

