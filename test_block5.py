import sqlite3
import datetime

def test_relatorio_mensal_metricas():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            cor TEXT DEFAULT '#10B981'
        );

        CREATE TABLE transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT NOT NULL,
            data_vencimento DATE NOT NULL,
            categoria_id INTEGER NOT NULL REFERENCES categorias(id),
            status TEXT DEFAULT 'Pendente'
        );

        CREATE TABLE orcamentos (
            ano_mes TEXT UNIQUE NOT NULL,
            limite_geral REAL NOT NULL DEFAULT 0
        );
    """)

    # Inserir categorias
    cursor.execute("INSERT INTO categorias (id, nome, tipo, cor) VALUES (1, 'Alimentação', 'Despesa', '#F59E0B')")
    cursor.execute("INSERT INTO categorias (id, nome, tipo, cor) VALUES (2, 'Transporte', 'Despesa', '#3B82F6')")
    cursor.execute("INSERT INTO categorias (id, nome, tipo, cor) VALUES (3, 'Salário', 'Receita', '#10B981')")

    # Inserir transações de Outubro/2026
    # Receita: 5000.00
    cursor.execute("INSERT INTO transacoes VALUES (1, 'receita', 5000.0, 'Salário Outubro', '2026-10-05', 3, 'Recebido')")
    
    # Despesas: Total = 2000.00
    # Alimentação: 1200.00 (60% do total de despesas) - 800 Pago, 400 Pendente
    cursor.execute("INSERT INTO transacoes VALUES (2, 'despesa', 800.0, 'Mercado Pago', '2026-10-10', 1, 'Pago')")
    cursor.execute("INSERT INTO transacoes VALUES (3, 'despesa', 400.0, 'Mercado Pendente', '2026-10-28', 1, 'Pendente')")
    
    # Transporte: 800.00 (40% do total de despesas) - 800 Pago
    cursor.execute("INSERT INTO transacoes VALUES (4, 'despesa', 800.0, 'Combustível', '2026-10-15', 2, 'Pago')")

    # 1. Totais Gerais do Mês (RF-03)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END), 0) as total_receitas,
            COALESCE(SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END), 0) as total_despesas
        FROM transacoes
        WHERE strftime('%Y-%m', data_vencimento) = '2026-10'
    """)
    rec, desp = cursor.fetchone()
    saldo = rec - desp
    assert rec == 5000.0
    assert desp == 2000.0
    assert saldo == 3000.0

    # 2. Destaque Contas Pendentes vs Pagas (RF-03)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'Pago' THEN valor ELSE 0 END), 0) as total_pago,
            COALESCE(SUM(CASE WHEN status = 'Pendente' THEN valor ELSE 0 END), 0) as total_pendente
        FROM transacoes
        WHERE tipo = 'despesa' AND strftime('%Y-%m', data_vencimento) = '2026-10'
    """)
    pago, pendente = cursor.fetchone()
    assert pago == 1600.0   # 800 + 800
    assert pendente == 400.0 # 400
    perc_pago = (pago / desp) * 100
    perc_pendente = (pendente / desp) * 100
    assert perc_pago == 80.0
    assert perc_pendente == 20.0

    # 3. Consolidação por Categoria com Percentual de Representatividade (RF-03)
    cursor.execute("""
        SELECT 
            c.nome, 
            SUM(t.valor) as total_categoria,
            ROUND((SUM(t.valor) * 100.0) / ?, 2) as percentual
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.tipo = 'despesa' AND strftime('%Y-%m', t.data_vencimento) = '2026-10'
        GROUP BY c.id
        ORDER BY total_categoria DESC
    """, (desp,))
    categorias_gastos = cursor.fetchall()
    
    assert len(categorias_gastos) == 2
    # Alimentação = 1200 / 2000 = 60.0%
    assert categorias_gastos[0][0] == 'Alimentação'
    assert categorias_gastos[0][1] == 1200.0
    assert categorias_gastos[0][2] == 60.0

    # Transporte = 800 / 2000 = 40.0%
    assert categorias_gastos[1][0] == 'Transporte'
    assert categorias_gastos[1][1] == 800.0
    assert categorias_gastos[1][2] == 40.0

    print("[PASS] 1. Métricas financeiras e consolidação por categoria com percentuais validados.")
    print("[PASS] 2. Destaque de contas Pagas vs Pendentes com divisão proporcional validado.")

def test_saldo_acumulado_conta():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            data_vencimento DATE NOT NULL,
            status TEXT NOT NULL
        );
    """)

    # Setembro: Receita recebida 3000, Despesa paga 2500 -> Sobrou 500
    cursor.execute("INSERT INTO transacoes VALUES (1, 'receita', 3000.0, '2026-09-05', 'Recebido')")
    cursor.execute("INSERT INTO transacoes VALUES (2, 'despesa', 2500.0, '2026-09-10', 'Pago')")

    # Outubro: Receita recebida 4000, Despesa paga 3000 -> Sobrou 1000
    cursor.execute("INSERT INTO transacoes VALUES (3, 'receita', 4000.0, '2026-10-05', 'Recebido')")
    cursor.execute("INSERT INTO transacoes VALUES (4, 'despesa', 3000.0, '2026-10-10', 'Pago')")
    # Despesa pendente que ainda nao saiu da conta: 500
    cursor.execute("INSERT INTO transacoes VALUES (5, 'despesa', 500.0, '2026-10-25', 'Pendente')")

    # Saldo acumulado em conta corrente ate Outubro (efetivado):
    # Setembro (500) + Outubro efetivado (1000) = 1500
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN tipo = 'receita' AND status IN ('Recebido', 'Pago') THEN valor ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN tipo = 'despesa' AND status = 'Pago' THEN valor ELSE 0 END), 0)
        FROM transacoes
        WHERE strftime('%Y-%m', data_vencimento) <= '2026-10'
    """)
    saldo_conta = cursor.fetchone()[0]
    assert saldo_conta == 1500.0
    print("[PASS] 3. Saldo acumulado em conta corrente (meses anteriores + mês vigente) validado.")

if __name__ == '__main__':
    test_relatorio_mensal_metricas()
    test_saldo_acumulado_conta()
    print("\nTODOS OS TESTES DO BLOCO 5 (RF-03 RELATÓRIO E ANÁLISE) PASSARAM! [100%]")

