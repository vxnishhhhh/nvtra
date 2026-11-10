"""Generate a secret-free WSGI entry point for a free PythonAnywhere web app."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def wsgi_source(domain, root=ROOT, data=None):
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:eu\.)?pythonanywhere\.com', domain):
        raise ValueError('Use the exact free *.pythonanywhere.com domain shown in the Web tab.')
    root = Path(root).resolve()
    data = Path(data).resolve() if data else Path.home() / '.local/share/nvtra'
    if data == root or root in data.parents:
        raise ValueError('Private data must be outside the repository/public files.')
    return (f'"""NVTRA free hosting: generated configuration, no credentials."""\n'
            f'import os\nimport sys\n'
            f'sys.path.insert(0, {str(root)!r})\n'
            f'os.environ["NVTRA_PUBLIC_URL"] = {("https://" + domain)!r}\n'
            f'os.environ["NVTRA_DATA_DIR"] = {str(data)!r}\n'
            'from app import application\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domain', required=True, help='Exact free domain from the PythonAnywhere Web tab')
    parser.add_argument('--output', type=Path, default=Path.home() / 'nvtra_wsgi.py')
    args = parser.parse_args()
    source = wsgi_source(args.domain)
    # Never overwrite an existing hosting configuration or its private settings.
    with args.output.open('x') as output:
        output.write(source)
    print(f'Created {args.output}. Copy its contents into the Web tab WSGI file, then Reload.')
    print('No package installation, paid plan, disk add-on or background server is required.')
