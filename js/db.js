// db.js - Camada de Dados SQLite (sql.js) com Persistência em IndexedDB

const IDB_NAME = 'FinControl_IDB';
const IDB_STORE = 'sqlite_storage';
const IDB_KEY = 'sqlite_database_bytes';

let dbInstance = null;
let sqlEngine = null;

/**
 * Abre conexão com o IndexedDB do navegador
 */
function openIDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(IDB_NAME, 1);
        request.onupgradeneeded = (e) => {
            const idb = e.target.result;
            if (!idb.objectStoreNames.contains(IDB_STORE)) {
                idb.createObjectStore(IDB_STORE);
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

/**
 * Recupera o arquivo binário do SQLite salvo no IndexedDB
 */
async function loadBytesFromIDB() {
    const idb = await openIDB();
    return new Promise((resolve, reject) => {
        const tx = idb.transaction(IDB_STORE, 'readonly');
        const store = tx.objectStore(IDB_STORE);
        const req = store.get(IDB_KEY);
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => reject(req.error);
    });
}

/**
 * Salva o arquivo binário do SQLite no IndexedDB
 */
async function saveBytesToIDB(bytes) {
    const idb = await openIDB();
    return new Promise((resolve, reject) => {
        const tx = idb.transaction(IDB_STORE, 'readwrite');
        const store = tx.objectStore(IDB_STORE);
        const req = store.put(bytes, IDB_KEY);
        req.onsuccess = () => resolve(true);
        req.onerror = () => reject(req.error);
    });
}

/**
 * Inicializa a engine do sql.js e carrega ou cria o banco SQLite
 */
async function initDatabase() {
    if (dbInstance) return dbInstance;

    try {
        sqlEngine = await initSqlJs({
            locateFile: (file) => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/${file}`
        });

        const savedBytes = await loadBytesFromIDB();

        if (savedBytes && savedBytes.length > 0) {
            dbInstance = new sqlEngine.Database(new Uint8Array(savedBytes));
            console.log('[SQLite] Banco de dados carregado com sucesso do IndexedDB.');
            garantirMigracoes(dbInstance);
            await persistirBanco();
        } else {
            console.log('[SQLite] Criando novo banco de dados SQLite local...');
            dbInstance = new sqlEngine.Database();
            criarEstruturaInicial(dbInstance);
            await persistirBanco();
        }

        return dbInstance;
    } catch (error) {
        console.error('[SQLite] Erro ao inicializar banco SQLite:', error);
        throw error;
    }
}

/**
 * Migrações e compatibilidade com bancos já inicializados
 */
function garantirMigracoes(db) {
    db.run(`
        CREATE TABLE IF NOT EXISTS investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Renda Fixa', 'Renda Variável', 'Fundos', 'Outros')),
            data_aporte DATE NOT NULL,
            observacoes TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano_mes TEXT UNIQUE NOT NULL,
            limite_geral REAL NOT NULL DEFAULT 0,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS limites_categoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano_mes TEXT NOT NULL,
            categoria_id INTEGER NOT NULL REFERENCES categorias(id) ON DELETE CASCADE,
            teto REAL NOT NULL,
            UNIQUE(ano_mes, categoria_id)
        );
    `);

    db.run(`UPDATE categorias SET nome = 'Investimento (Patrimônio)' WHERE nome = 'Investimentos' AND tipo = 'Receita';`);
}

/**
 * Criação do schema inicial de tabelas e categorias padrão (RF-01, RF-02 e Investimentos)
 */
function criarEstruturaInicial(db) {
    db.run(`
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Receita', 'Despesa')),
            icone TEXT DEFAULT 'fa-tag',
            cor TEXT DEFAULT '#10B981',
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS transacoes (
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

        CREATE TABLE IF NOT EXISTS investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Renda Fixa', 'Renda Variável', 'Fundos', 'Outros')),
            data_aporte DATE NOT NULL,
            observacoes TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano_mes TEXT UNIQUE NOT NULL,
            limite_geral REAL NOT NULL DEFAULT 0,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS limites_categoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano_mes TEXT NOT NULL,
            categoria_id INTEGER NOT NULL REFERENCES categorias(id) ON DELETE CASCADE,
            teto REAL NOT NULL,
            UNIQUE(ano_mes, categoria_id)
        );

        CREATE INDEX IF NOT EXISTS idx_transacoes_data ON transacoes(data_vencimento);
        CREATE INDEX IF NOT EXISTS idx_transacoes_tipo ON transacoes(tipo);
        CREATE INDEX IF NOT EXISTS idx_transacoes_status ON transacoes(status);
        CREATE INDEX IF NOT EXISTS idx_investimentos_tipo ON investimentos(tipo);
    `);

    // Inserção das Categorias Padrão com ajuste do Investimento (Patrimônio)
    const categoriasIniciais = [
        // Receitas
        { nome: 'Salário', tipo: 'Receita', icone: 'fa-briefcase', cor: '#10B981' },
        { nome: 'Investimento (Patrimônio)', tipo: 'Receita', icone: 'fa-piggy-bank', cor: '#3B82F6' },
        { nome: 'Outras Receitas', tipo: 'Receita', icone: 'fa-wallet', cor: '#059669' },
        // Despesas
        { nome: 'Alimentação', tipo: 'Despesa', icone: 'fa-utensils', cor: '#F59E0B' },
        { nome: 'Transporte', tipo: 'Despesa', icone: 'fa-car', cor: '#3B82F6' },
        { nome: 'Saúde', tipo: 'Despesa', icone: 'fa-heart-pulse', cor: '#EF4444' },
        { nome: 'Lazer', tipo: 'Despesa', icone: 'fa-gamepad', cor: '#EC4899' },
        { nome: 'Moradia', tipo: 'Despesa', icone: 'fa-house', cor: '#8B5CF6' },
        { nome: 'Outras Despesas', tipo: 'Despesa', icone: 'fa-receipt', cor: '#64748B' }
    ];

    const stmt = db.prepare(`INSERT INTO categorias (nome, tipo, icone, cor) VALUES (?, ?, ?, ?)`);
    for (const cat of categoriasIniciais) {
        stmt.run([cat.nome, cat.tipo, cat.icone, cat.cor]);
    }
    stmt.free();

    const hoje = new Date();
    const anoMes = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}`;
    db.run(`INSERT OR IGNORE INTO orcamentos (ano_mes, limite_geral) VALUES (?, ?)`, [anoMes, 4000.00]);

    console.log('[SQLite] Estrutura completa, categorias e limites inicializados.');
}

/**
 * Persiste o estado atual do SQLite no IndexedDB do navegador
 */
async function persistirBanco() {
    if (!dbInstance) return;
    const data = dbInstance.export();
    await saveBytesToIDB(data);
}

/**
 * Executa uma consulta SQL (SELECT) e retorna array de objetos
 */
function querySQL(sql, params = []) {
    if (!dbInstance) throw new Error('Banco SQLite não inicializado.');
    const stmt = dbInstance.prepare(sql);
    if (params.length > 0) stmt.bind(params);
    
    const rows = [];
    while (stmt.step()) {
        rows.push(stmt.getAsObject());
    }
    stmt.free();
    return rows;
}

/**
 * Executa um comando SQL (INSERT, UPDATE, DELETE) e persiste automaticamente
 */
async function executeSQL(sql, params = []) {
    if (!dbInstance) throw new Error('Banco SQLite não inicializado.');
    dbInstance.run(sql, params);
    await persistirBanco();
}

// ==========================================
// FUNÇÕES DE CRUD: CATEGORIAS (RF-01)
// ==========================================

function obterCategorias(tipo = null) {
    let sql = "SELECT * FROM categorias";
    const params = [];
    if (tipo) {
        sql += " WHERE tipo = ?";
        params.push(tipo);
    }
    sql += " ORDER BY nome ASC";
    return querySQL(sql, params);
}

async function salvarCategoria({ id, nome, tipo, icone, cor }) {
    if (!nome || !tipo) throw new Error('Nome e tipo são obrigatórios para a categoria.');
    icone = icone || 'fa-tag';
    cor = cor || '#10B981';

    if (id) {
        await executeSQL(`
            UPDATE categorias 
            SET nome = ?, tipo = ?, icone = ?, cor = ? 
            WHERE id = ?
        `, [nome, tipo, icone, cor, id]);
    } else {
        await executeSQL(`
            INSERT INTO categorias (nome, tipo, icone, cor) 
            VALUES (?, ?, ?, ?)
        `, [nome, tipo, icone, cor]);
    }
}

async function excluirCategoria(id) {
    const uso = querySQL("SELECT COUNT(*) as count FROM transacoes WHERE categoria_id = ?", [id])[0];
    if (uso && uso.count > 0) {
        throw new Error(`Não é possível excluir: existem ${uso.count} lançamento(s) vinculados a esta categoria.`);
    }
    await executeSQL("DELETE FROM categorias WHERE id = ?", [id]);
}

// ==========================================
// FUNÇÕES DE CRUD: TRANSAÇÕES (RF-02 & BLOCO 3/4)
// ==========================================

function obterTransacoes({ anoMes = null, tipo = null, status = null, busca = null, categoriaId = null } = {}) {
    let sql = `
        SELECT t.*, c.nome as categoria_nome, c.icone as categoria_icone, c.cor as categoria_cor
        FROM transacoes t
        LEFT JOIN categorias c ON t.categoria_id = c.id
        WHERE 1=1
    `;
    const params = [];

    if (anoMes) {
        sql += " AND strftime('%Y-%m', t.data_vencimento) = ?";
        params.push(anoMes);
    }

    if (tipo && tipo !== 'todos') {
        sql += " AND t.tipo = ?";
        params.push(tipo);
    }

    if (status && status !== 'todos') {
        sql += " AND t.status = ?";
        params.push(status);
    }

    if (categoriaId) {
        sql += " AND t.categoria_id = ?";
        params.push(categoriaId);
    }

    if (busca && busca.trim()) {
        sql += " AND (t.descricao LIKE ? OR c.nome LIKE ? OR t.conta LIKE ?)";
        const termo = `%${busca.trim()}%`;
        params.push(termo, termo, termo);
    }

    sql += " ORDER BY t.data_vencimento DESC, t.id DESC";
    return querySQL(sql, params);
}

function obterTransacaoPorId(id) {
    const res = querySQL(`
        SELECT t.*, c.nome as categoria_nome, c.icone as categoria_icone, c.cor as categoria_cor
        FROM transacoes t
        LEFT JOIN categorias c ON t.categoria_id = c.id
        WHERE t.id = ?
    `, [id]);
    return res.length > 0 ? res[0] : null;
}

async function salvarTransacao({ id, tipo, valor, descricao, data_vencimento, categoria_id, status, data_pagamento, conta, observacoes }) {
    if (!tipo || !valor || !descricao || !data_vencimento || !categoria_id) {
        throw new Error('Preencha todos os campos obrigatórios da transação.');
    }

    status = status || 'Pendente';
    conta = conta || 'Carteira Principal';
    observacoes = observacoes || '';

    // Se marcado como Pago/Recebido e não tem data de pagamento, usa a de vencimento
    if ((status === 'Pago' || status === 'Recebido') && !data_pagamento) {
        data_pagamento = data_vencimento;
    }

    if (id) {
        await executeSQL(`
            UPDATE transacoes
            SET tipo = ?, valor = ?, descricao = ?, data_vencimento = ?, categoria_id = ?, status = ?, data_pagamento = ?, conta = ?, observacoes = ?
            WHERE id = ?
        `, [tipo, valor, descricao, data_vencimento, categoria_id, status, data_pagamento, conta, observacoes, id]);
    } else {
        await executeSQL(`
            INSERT INTO transacoes (tipo, valor, descricao, data_vencimento, categoria_id, status, data_pagamento, conta, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `, [tipo, valor, descricao, data_vencimento, categoria_id, status, data_pagamento, conta, observacoes]);
    }
}

async function alternarStatusTransacao(id) {
    const t = obterTransacaoPorId(id);
    if (!t) throw new Error('Transação não encontrada.');

    let novoStatus;
    let novaDataPagamento = t.data_pagamento;

    if (t.status === 'Pendente') {
        novoStatus = t.tipo === 'receita' ? 'Recebido' : 'Pago';
        novaDataPagamento = new Date().toISOString().split('T')[0];
    } else {
        novoStatus = 'Pendente';
        novaDataPagamento = null;
    }

    await executeSQL(`
        UPDATE transacoes
        SET status = ?, data_pagamento = ?
        WHERE id = ?
    `, [novoStatus, novaDataPagamento, id]);

    return novoStatus;
}

async function excluirTransacao(id) {
    await executeSQL("DELETE FROM transacoes WHERE id = ?", [id]);
}

// ==========================================
// FUNÇÕES DE CRUD: INVESTIMENTOS (PATRIMÔNIO)
// ==========================================

function obterInvestimentos() {
    return querySQL("SELECT * FROM investimentos ORDER BY data_aporte DESC, id DESC");
}

function obterTotalInvestimentos() {
    const res = querySQL("SELECT COALESCE(SUM(valor), 0) as total FROM investimentos")[0];
    return res ? res.total : 0;
}

async function salvarInvestimento({ id, nome, valor, tipo, data_aporte, observacoes }) {
    if (!nome || !valor || !tipo || !data_aporte) {
        throw new Error('Todos os campos obrigatórios do investimento devem ser preenchidos.');
    }
    observacoes = observacoes || '';

    if (id) {
        await executeSQL(`
            UPDATE investimentos
            SET nome = ?, valor = ?, tipo = ?, data_aporte = ?, observacoes = ?
            WHERE id = ?
        `, [nome, valor, tipo, data_aporte, observacoes, id]);
    } else {
        await executeSQL(`
            INSERT INTO investimentos (nome, valor, tipo, data_aporte, observacoes)
            VALUES (?, ?, ?, ?, ?)
        `, [nome, valor, tipo, data_aporte, observacoes]);
    }
}

async function excluirInvestimento(id) {
    await executeSQL("DELETE FROM investimentos WHERE id = ?", [id]);
}

// ==========================================
// FUNÇÕES: ORÇAMENTO / TETO DE GASTOS
// ==========================================

function obterOrcamentoMes(anoMes) {
    const res = querySQL("SELECT limite_geral FROM orcamentos WHERE ano_mes = ?", [anoMes])[0];
    return res ? res.limite_geral : 0;
}

async function definirOrcamentoMes(anoMes, limiteGeral) {
    await executeSQL(`
        INSERT INTO orcamentos (ano_mes, limite_geral)
        VALUES (?, ?)
        ON CONFLICT(ano_mes) DO UPDATE SET limite_geral = excluded.limite_geral
    `, [anoMes, limiteGeral]);
}

// ==========================================
// FUNÇÕES: RELATÓRIO E ANÁLISE MENSAL (RF-03)
// ==========================================

function obterSaldoAcumuladoConta(anoMesLimite = null) {
    let sql = `
        SELECT 
            COALESCE(SUM(CASE WHEN tipo = 'receita' AND status IN ('Recebido', 'Pago') THEN valor ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN tipo = 'despesa' AND status = 'Pago' THEN valor ELSE 0 END), 0) as saldo_acumulado
        FROM transacoes
    `;
    const params = [];
    if (anoMesLimite) {
        sql += " WHERE strftime('%Y-%m', data_vencimento) <= ?";
        params.push(anoMesLimite);
    }
    const res = querySQL(sql, params)[0];
    return res ? res.saldo_acumulado : 0;
}

function obterDadosRelatorioMensal(anoMes) {
    const totais = querySQL(`
        SELECT 
            COALESCE(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END), 0) as total_receitas,
            COALESCE(SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END), 0) as total_despesas
        FROM transacoes
        WHERE strftime('%Y-%m', data_vencimento) = ?
    `, [anoMes])[0] || { total_receitas: 0, total_despesas: 0 };

    const despesasStatus = querySQL(`
        SELECT 
            COALESCE(SUM(CASE WHEN status = 'Pago' THEN valor ELSE 0 END), 0) as total_pago,
            COALESCE(SUM(CASE WHEN status = 'Pendente' THEN valor ELSE 0 END), 0) as total_pendente,
            COUNT(CASE WHEN status = 'Pago' THEN 1 END) as qtd_pago,
            COUNT(CASE WHEN status = 'Pendente' THEN 1 END) as qtd_pendente
        FROM transacoes
        WHERE tipo = 'despesa' AND strftime('%Y-%m', data_vencimento) = ?
    `, [anoMes])[0] || { total_pago: 0, total_pendente: 0, qtd_pago: 0, qtd_pendente: 0 };

    const categoriasDespesas = querySQL(`
        SELECT 
            c.id, c.nome, c.icone, c.cor,
            SUM(t.valor) as total,
            COUNT(t.id) as quantidade
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        WHERE t.tipo = 'despesa' AND strftime('%Y-%m', t.data_vencimento) = ?
        GROUP BY c.id
        ORDER BY total DESC
    `, [anoMes]);

    const categoriasComPercentual = categoriasDespesas.map(cat => ({
        ...cat,
        percentual: totais.total_despesas > 0 ? ((cat.total / totais.total_despesas) * 100) : 0
    }));

    return {
        anoMes,
        totalReceitas: totais.total_receitas,
        totalDespesas: totais.total_despesas,
        saldo: totais.total_receitas - totais.total_despesas,
        despesasPagas: despesasStatus.total_pago,
        despesasPendentes: despesasStatus.total_pendente,
        qtdPagas: despesasStatus.qtd_pago,
        qtdPendentes: despesasStatus.qtd_pendente,
        categorias: categoriasComPercentual
    };
}

// ==========================================
// FUNÇÕES: BACKUP E RESTAURAÇÃO (RF-04)
// ==========================================

function exportarArquivoSQLite() {
    if (!dbInstance) throw new Error('Banco SQLite não inicializado.');
    const binaryData = dbInstance.export();
    const blob = new Blob([binaryData], { type: 'application/x-sqlite3' });
    const url = URL.createObjectURL(blob);
    
    const dataAtual = new Date().toISOString().split('T')[0];
    const a = document.createElement('a');
    a.href = url;
    a.download = `fincontrol_backup_${dataAtual}.sqlite`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Estatísticas do banco atual para o painel de Backup (RF-04)
 */
function obterEstatisticasBanco() {
    if (!dbInstance) throw new Error('Banco SQLite não inicializado.');
    const contar = (tabela) => querySQL(`SELECT COUNT(*) as total FROM ${tabela}`)[0].total;
    return {
        transacoes: contar('transacoes'),
        categorias: contar('categorias'),
        investimentos: contar('investimentos'),
        orcamentos: contar('orcamentos'),
        tamanhoBytes: dbInstance.export().length
    };
}

/**
 * Verifica a assinatura "SQLite format 3" + byte nulo nos primeiros 16 bytes do arquivo
 */
function possuiCabecalhoSQLite(bytes) {
    const assinatura = 'SQLite format 3' + String.fromCharCode(0);
    if (bytes.length < assinatura.length) return false;
    for (let i = 0; i < assinatura.length; i++) {
        if (bytes[i] !== assinatura.charCodeAt(i)) return false;
    }
    return true;
}

async function restaurarArquivoSQLite(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = async () => {
            let novoBanco = null;
            try {
                const uInt8Array = new Uint8Array(reader.result);
                if (!possuiCabecalhoSQLite(uInt8Array)) {
                    throw new Error('O arquivo selecionado não é um banco SQLite.');
                }

                novoBanco = new sqlEngine.Database(uInt8Array);

                const check = novoBanco.exec("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('categorias', 'transacoes');");
                if (!check || check.length === 0 || check[0].values.length < 2) {
                    throw new Error('O arquivo selecionado não é um backup válido do FinControl.');
                }

                garantirMigracoes(novoBanco);

                // Troca o banco ativo e libera a memória do anterior
                const bancoAnterior = dbInstance;
                dbInstance = novoBanco;
                novoBanco = null;
                if (bancoAnterior) bancoAnterior.close();

                await persistirBanco();
                console.log('[SQLite] Banco restaurado com sucesso.');
                resolve(true);
            } catch (err) {
                if (novoBanco) novoBanco.close();
                reject(err);
            }
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsArrayBuffer(file);
    });
}
