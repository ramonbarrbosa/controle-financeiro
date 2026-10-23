"""
Gera css/tailwind.css a partir de index.html e js/ usando o Tailwind CSS Standalone CLI
(executável único, sem necessidade de Node.js).

Uso:
    python build_css.py          # gera o CSS minificado
    python build_css.py --watch  # regera automaticamente ao salvar arquivos

O executável é baixado na primeira execução para a pasta tools/ (ignorada pelo Git).
"""
import os
import platform
import subprocess
import sys
import urllib.request

TAILWIND_VERSION = 'v3.4.17'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, 'tools')
INPUT_CSS = os.path.join('css', 'input.css')
OUTPUT_CSS = os.path.join('css', 'tailwind.css')


def nome_binario():
    sistema = platform.system().lower()
    arquitetura = 'arm64' if platform.machine().lower() in ('arm64', 'aarch64') else 'x64'
    if sistema == 'windows':
        return f'tailwindcss-windows-{arquitetura}.exe'
    if sistema == 'darwin':
        return f'tailwindcss-macos-{arquitetura}'
    return f'tailwindcss-linux-{arquitetura}'


def caminho_binario():
    return os.path.join(TOOLS_DIR, f'{TAILWIND_VERSION}-{nome_binario()}')


def garantir_binario():
    destino = caminho_binario()
    if os.path.exists(destino):
        return destino

    os.makedirs(TOOLS_DIR, exist_ok=True)
    url = f'https://github.com/tailwindlabs/tailwindcss/releases/download/{TAILWIND_VERSION}/{nome_binario()}'
    print(f'[build_css] Baixando Tailwind CLI {TAILWIND_VERSION}...')
    temporario = destino + '.download'
    urllib.request.urlretrieve(url, temporario)
    os.replace(temporario, destino)
    if platform.system().lower() != 'windows':
        os.chmod(destino, 0o755)
    return destino


def gerar_css(saida=OUTPUT_CSS, watch=False):
    comando = [garantir_binario(), '-c', 'tailwind.config.js', '-i', INPUT_CSS, '-o', saida, '--minify']
    if watch:
        comando.append('--watch')
    subprocess.run(comando, cwd=BASE_DIR, check=True)


if __name__ == '__main__':
    gerar_css(watch='--watch' in sys.argv)
    print(f'[build_css] CSS gerado em {OUTPUT_CSS}')
