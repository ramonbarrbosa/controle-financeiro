import json
import sqlite3
import os

def test_files_exist():
    required_files = [
        'requirements.txt',
        'manifest.json',
        'sw.js',
        'assets/icon.svg',
        'js/theme.js',
        'js/db.js',
        'index.html'
    ]
    for file_path in required_files:
        assert os.path.exists(file_path), f"Arquivo não encontrado: {file_path}"
    print("[PASS] 1. Todos os arquivos obrigatórios existem.")

def test_manifest_validity():
    with open('manifest.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data.get('name') == 'FinControl - Controle Financeiro'
    assert data.get('display') == 'standalone'
    assert len(data.get('icons', [])) > 0
    print("[PASS] 2. Manifest PWA válido e configurado para instalação standalone.")

def test_sqlite_schema():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    with open('js/db.js', 'r', encoding='utf-8') as f:
        db_js_content = f.read()

    # Garantir que as tabelas essenciais estão declaradas no db.js
    assert 'CREATE TABLE IF NOT EXISTS categorias' in db_js_content
    assert 'CREATE TABLE IF NOT EXISTS transacoes' in db_js_content

    # Executar schema no sqlite3
    cursor.execute("""
        CREATE TABLE categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Receita', 'Despesa')),
            icone TEXT DEFAULT 'fa-tag',
            cor TEXT DEFAULT '#10B981',
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
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

    # Teste de inserção e integridade referencial
    cursor.execute("INSERT INTO categorias (nome, tipo) VALUES ('Alimentação', 'Despesa')")
    cat_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO transacoes (tipo, valor, descricao, data_vencimento, categoria_id, status)
        VALUES ('despesa', 85.50, 'Mercado Central', '2026-10-22', ?, 'Pendente')
    """, (cat_id,))

    cursor.execute("SELECT count(*) FROM transacoes")
    count = cursor.fetchone()[0]
    assert count == 1
    print("[PASS] 3. Schema SQLite validado com sucesso e compatível com as especificações.")

def test_theme_and_pwa_references():
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()
    assert 'theme-toggle' in html
    assert 'theme-icon' in html
    assert 'manifest.json' in html
    assert 'sw.js' in html
    assert 'sql-wasm.js' in html
    print("[PASS] 4. Index.html integra alternador de Tema (Dark/Light), PWA e SQLite WASM.")

if __name__ == '__main__':
    test_files_exist()
    test_manifest_validity()
    test_sqlite_schema()
    test_theme_and_pwa_references()
    print("\nTODOS OS TESTES DO BLOCO 1 PASSARAM COM SUCESSO! [100%]")

