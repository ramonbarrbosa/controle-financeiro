import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UM_DIA_MS = 24 * 60 * 60 * 1000
AGORA = 1_793_000_000_000  # instante fixo de referência (ms)


def ler_arquivo(nome):
    with open(os.path.join(BASE_DIR, nome), encoding='utf-8') as f:
        return f.read()


# Espelha avaliarLembreteBackup() do index.html
def avaliar_lembrete_backup(ultimo_backup, adiado_ate, prazo_dias, total_lancamentos, agora=AGORA):
    if not prazo_dias:
        return {'mostrar': False, 'diasDesde': None}
    if adiado_ate and agora < adiado_ate:
        return {'mostrar': False, 'diasDesde': None}
    if not ultimo_backup:
        return {'mostrar': total_lancamentos > 0, 'diasDesde': None}
    dias_desde = (agora - ultimo_backup) // UM_DIA_MS
    return {'mostrar': dias_desde >= prazo_dias, 'diasDesde': dias_desde}


# Cenários compartilhados com o teste no navegador: (descrição, entrada, mostrar, diasDesde)
CENARIOS = [
    ('nunca fez backup e sem lançamentos', (None, None, 7, 0), False, None),
    ('nunca fez backup e com lançamentos', (None, None, 7, 3), True, None),
    ('backup há 3 dias (prazo 7)', (AGORA - 3 * UM_DIA_MS, None, 7, 10), False, 3),
    ('backup há exatamente 7 dias', (AGORA - 7 * UM_DIA_MS, None, 7, 10), True, 7),
    ('backup há 6 dias e 23h', (AGORA - 7 * UM_DIA_MS + 3_600_000, None, 7, 10), False, 6),
    ('backup há 10 dias (prazo 15)', (AGORA - 10 * UM_DIA_MS, None, 15, 10), False, 10),
    ('backup há 40 dias (prazo 30)', (AGORA - 40 * UM_DIA_MS, None, 30, 10), True, 40),
    ('vencido mas adiado até amanhã', (AGORA - 40 * UM_DIA_MS, AGORA + UM_DIA_MS, 7, 10), False, None),
    ('adiamento já expirado', (AGORA - 40 * UM_DIA_MS, AGORA - 1, 7, 10), True, 40),
    ('lembrete desativado', (None, None, 0, 10), False, None),
]


def test_cenarios_do_lembrete():
    for descricao, entrada, mostrar, dias in CENARIOS:
        r = avaliar_lembrete_backup(*entrada)
        assert r == {'mostrar': mostrar, 'diasDesde': dias}, (descricao, r)
    print(f"[PASS] 1. {len(CENARIOS)} cenários do lembrete (nunca, no prazo, vencido, adiado, desativado).")


def test_logica_js_espelhada():
    html = ler_arquivo('index.html')
    corpo = re.search(r'function avaliarLembreteBackup\(.*?\n        \}\n', html, re.S).group(0)
    for trecho in ('if (!prazoDias)', 'agora < adiadoAte', 'totalLancamentos > 0',
                   'Math.floor((agora - ultimoBackup) / UM_DIA_MS)', 'diasDesde >= prazoDias'):
        assert trecho in corpo, trecho
    assert re.search(r'const PRAZOS_LEMBRETE = \[0, 7, 15, 30\];', html)
    assert 'const PRAZO_LEMBRETE_PADRAO = 7;' in html
    print("[PASS] 2. Regras do JS conferem com o teste (prazos 7/15/30/desativado, padrão 7 dias).")


def test_interface_lembrete():
    html = ler_arquivo('index.html')
    for id_ in ('lembrete-backup', 'lembrete-backup-titulo', 'lembrete-backup-texto', 'backup-prazo-lembrete'):
        assert f'id="{id_}"' in html, id_
    opcoes = re.findall(r'<option value="(\d+)">', html[html.index('id="backup-prazo-lembrete"'):])[:4]
    assert opcoes == ['7', '15', '30', '0']

    for fn in ('adiarLembreteBackup', 'fazerBackupPeloLembrete', 'salvarPrazoLembreteBackup', 'atualizarLembreteBackup'):
        assert re.search(rf'function {fn}\(', html), fn

    # O aviso é reavaliado ao carregar dados e após exportar
    carregar = html[html.index('function carregarDadosApp('):html.index('function renderizarTransacoes(')]
    exportar = html[html.index('function executarExportacao('):html.index('function selecionarArquivoRestore(')]
    assert 'atualizarLembreteBackup()' in carregar
    assert 'atualizarLembreteBackup()' in exportar
    assert 'localStorage.setItem' not in exportar, 'Use gravarPreferencia() (protegido por try/catch)'
    print("[PASS] 3. Aviso no painel, configuração no modal e reavaliação após exportar.")


if __name__ == '__main__':
    test_cenarios_do_lembrete()
    test_logica_js_espelhada()
    test_interface_lembrete()
    print("\nTODOS OS TESTES DO BLOCO 9 (LEMBRETE DE BACKUP) PASSARAM! [100%]")
