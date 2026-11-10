"""Build a public, self-contained design preview; never copy private/server files."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def build(output=None):
    html = (ROOT / 'index.html').read_text()
    config = {'pricing': json.loads((ROOT / 'config/pricing.json').read_text()),
              'content': json.loads((ROOT / 'config/content.json').read_text()),
              'aiAvailable': False, 'emailAvailable': False, 'timezone': 'Africa/Johannesburg'}
    payload = json.dumps(config, ensure_ascii=True).replace('<', '\\u003c')
    html = html.replace('<script src="platform.js"></script>',
                        '<script>window.NVTRA_PREVIEW_CONFIG=' + payload + ';</script>\n<script src="platform.js"></script>')
    for name in ['studio', 'platform', 'cinematic']:
        css = (ROOT / (name + '.css')).read_text()
        js = (ROOT / (name + '.js')).read_text().replace('</script', '<\\/script')
        html = re.sub(r'<link[^>]+href="' + name + r'\.css"[^>]*>', lambda m: '<style>' + css + '</style>', html)
        html = html.replace('<script src="' + name + '.js"></script>', '<script>' + js + '</script>')
    html = html.replace('<head>', '<head>\n<meta name="robots" content="noindex,nofollow">', 1)
    html = html.replace('<title>NVTRA', '<title>Design preview | NVTRA', 1)
    target = Path(output) if output else ROOT / 'preview.html'
    target.write_text(html)
    return target


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    print(build(parser.parse_args().output))
