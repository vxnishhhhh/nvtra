"""Start the WSGI app on Render's port with its actual HTTPS origin."""
import os
import sys
from urllib.parse import urlsplit


def configure(environ):
    origin = (environ.get('NVTRA_PUBLIC_URL') or environ.get('RENDER_EXTERNAL_URL', '')).rstrip('/')
    parsed = urlsplit(origin)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or
            parsed.password or parsed.path or parsed.query or parsed.fragment):
        raise ValueError('Set NVTRA_PUBLIC_URL or RENDER_EXTERNAL_URL to the exact public HTTPS origin.')
    if not environ.get('NVTRA_DATA_DIR'):
        raise ValueError('Set NVTRA_DATA_DIR to the persistent private disk directory.')
    port = int(environ.get('PORT', '10000'))
    if not 1 <= port <= 65535:
        raise ValueError('PORT must be between 1 and 65535.')
    environ['NVTRA_PUBLIC_URL'] = origin
    return [sys.executable, '-m', 'waitress', f'--listen=0.0.0.0:{port}',
            '--threads=8', '--max-request-body-size=7340032', 'app:application']


if __name__ == '__main__':
    args = configure(os.environ)
    os.execv(sys.executable, args)
