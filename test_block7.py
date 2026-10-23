import os
import re
import tempfile

import build_css

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def ler_arquivo(nome):
    with open(os.path.join(BASE_DIR, nome), encoding='utf-8') as f:
        return f.read()


def test_cdn_removido():
    html = ler_arquivo('index.html')
    sw = ler_arquivo('sw.js')
    assert 'cdn.tailwindcss.com' not in html
    assert 'tailwind.config' not in html
    assert 'cdn.tailwindcss.com' not in sw
    assert '<link rel="stylesheet" href="./css/tailwind.css">' in html
    assert "'./css/tailwind.css'" in sw, 'CSS local deve estar no cache offline do Service Worker'
    print("[PASS] 1. CDN do Tailwind removido e CSS local referenciado no HTML e no Service Worker.")


def test_css_contem_classes_customizadas():
    css = ler_arquivo('css/tailwind.css')
    # Cores e fonte do tailwind.config.js, variantes dark: e peer-checked: usadas no app
    for seletor in (r'\.dark\\:bg-cardBg:is\(\.dark \*\)', r'\.dark\\:bg-darkBg', r'\.dark\\:hover\\:bg-cardHover',
                    r'\.peer:checked~\.peer-checked\\:bg-rose-500\\/20', r'\.backdrop-blur-sm'):
        assert re.search(seletor, css), f'Classe ausente no CSS gerado: {seletor}'
    assert 'Inter' in css
    print("[PASS] 2. CSS gerado contém cores, fonte e variantes customizadas.")


def test_css_atualizado():
    if not os.path.exists(build_css.caminho_binario()):
        print("[SKIP] 3. Tailwind CLI não baixado (rode `python build_css.py`).")
        return
    with tempfile.TemporaryDirectory() as tmp:
        saida = os.path.join(tmp, 'tailwind.css')
        build_css.gerar_css(saida=saida)
        with open(saida, encoding='utf-8') as f:
            novo = f.read()
    assert novo == ler_arquivo('css/tailwind.css'), \
        'css/tailwind.css desatualizado: rode `python build_css.py` e inclua o arquivo no commit.'
    print("[PASS] 3. css/tailwind.css está atualizado com as classes do HTML/JS.")


if __name__ == '__main__':
    test_cdn_removido()
    test_css_contem_classes_customizadas()
    test_css_atualizado()
    print("\nTODOS OS TESTES DO BLOCO 7 (TAILWIND LOCAL) PASSARAM! [100%]")
