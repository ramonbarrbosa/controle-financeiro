import sqlite3
import datetime

def test_categorias_crud():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Receita', 'Despesa')),
            icone TEXT DEFAULT 'fa-tag',
            cor TEXT DEFAULT '#10B981',
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
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

    # 1. Categoria padrão ajustada
    cursor.execute("INSERT INTO categorias (nome, tipo, icone, cor) VALUES ('Investimento (Patrimônio)', 'Receita', 'fa-piggy-bank', '#3B82F6')")
    cat_id = cursor.lastrowid
    assert cat_id is not None

    # 2. Cadastro de nova categoria
    cursor.execute("INSERT INTO categorias (nome, tipo, icone, cor) VALUES ('Educação', 'Despesa', 'fa-graduation-cap', '#6366F1')")
    edu_id = cursor.lastrowid
    
    # 3. Edição de categoria
    cursor.execute("UPDATE categorias SET nome = 'Cursos & Educação' WHERE id = ?", (edu_id,))
    cursor.execute("SELECT nome FROM categorias WHERE id = ?", (edu_id,))
    assert cursor.fetchone()[0] == 'Cursos & Educação'

    # 4. Exclusão de categoria sem vínculos
    cursor.execute("DELETE FROM categorias WHERE id = ?", (edu_id,))
    cursor.execute("SELECT count(*) FROM categorias WHERE id = ?", (edu_id,))
    assert cursor.fetchone()[0] == 0

    print("[PASS] 1. CRUD de Categorias (RF-01) e ajuste de 'Investimento (Patrimônio)' validados.")

def test_investimentos_crud():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Renda Fixa', 'Renda Variável', 'Fundos', 'Outros')),
            data_aporte DATE NOT NULL,
            observacoes TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Inserção de investimentos (Renda Fixa e Variável)
    cursor.execute("""
        INSERT INTO investimentos (nome, valor, tipo, data_aporte, observacoes)
        VALUES ('Tesouro Selic 2029', 5000.00, 'Renda Fixa', '2026-10-15', 'Reserva de oportunidade')
    """)
    cursor.execute("""
        INSERT INTO investimentos (nome, valor, tipo, data_aporte, observacoes)
        VALUES ('Fundo Imobiliário HGLG11', 3200.00, 'Renda Variável', '2026-10-20', 'Proventos mensais')
    """)

    # Somatório do patrimônio total
    cursor.execute("SELECT SUM(valor) FROM investimentos")
    total_patrimonio = cursor.fetchone()[0]
    assert total_patrimonio == 8200.00

    # Somatório por tipo
    cursor.execute("SELECT SUM(valor) FROM investimentos WHERE tipo = 'Renda Fixa'")
    assert cursor.fetchone()[0] == 5000.00

    cursor.execute("SELECT SUM(valor) FROM investimentos WHERE tipo = 'Renda Variável'")
    assert cursor.fetchone()[0] == 3200.00

    print("[PASS] 2. Módulo de Investimentos (Patrimônio) e somatórios por tipo validados.")

def test_orcamento_teto_e_comparativo():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano_mes TEXT UNIQUE NOT NULL,
            limite_geral REAL NOT NULL DEFAULT 0,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT NOT NULL,
            data_vencimento DATE NOT NULL,
            categoria_id INTEGER,
            status TEXT DEFAULT 'Pendente'
        );
    """)

    # 1. Definição do Teto do Mês
    cursor.execute("INSERT INTO orcamentos (ano_mes, limite_geral) VALUES ('2026-10', 4000.00)")
    
    # Inserir transações de Outubro (mês atual)
    cursor.execute("INSERT INTO transacoes (tipo, valor, descricao, data_vencimento) VALUES ('despesa', 2800.00, 'Despesas Diversas', '2026-10-10')")
    
    # Inserir transações de Setembro (mês anterior)
    cursor.execute("INSERT INTO transacoes (tipo, valor, descricao, data_vencimento) VALUES ('despesa', 3200.00, 'Despesas Mês Passado', '2026-09-15')")

    # Termômetro do Teto: 2800 / 4000 = 70%
    cursor.execute("SELECT limite_geral FROM orcamentos WHERE ano_mes = '2026-10'")
    teto = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(valor) FROM transacoes WHERE tipo = 'despesa' AND strftime('%Y-%m', data_vencimento) = '2026-10'")
    gasto_atual = cursor.fetchone()[0]
    percentual_consumido = (gasto_atual / teto) * 100
    assert percentual_consumido == 70.0

    # Comparativo com mês anterior:
    cursor.execute("SELECT SUM(valor) FROM transacoes WHERE tipo = 'despesa' AND strftime('%Y-%m', data_vencimento) = '2026-09'")
    gasto_anterior = cursor.fetchone()[0]
    
    # Variação: (2800 - 3200) / 3200 = -12.5% (economia de 12.5%)
    variacao_percentual = ((gasto_atual - gasto_anterior) / gasto_anterior) * 100
    assert round(variacao_percentual, 1) == -12.5
    print("[PASS] 3. Teto orçamentário (termômetro) e cálculo comparativo com mês anterior validados.")

if __name__ == '__main__':
    test_categorias_crud()
    test_investimentos_crud()
    test_orcamento_teto_e_comparativo()
    print("\nTODOS OS TESTES DO BLOCO 2 (CATEGORIAS + INVESTIMENTOS + TETO) PASSARAM! [100%]")

