from pathlib import Path
import tempfile
import unittest
from scripts.build_preview import ROOT, build


class PreviewBuild(unittest.TestCase):
    def test_self_contained_and_current_without_server_source(self):
        with tempfile.TemporaryDirectory() as directory:
            output = build(Path(directory) / 'preview.html')
            html = output.read_text()
        self.assertEqual(html, (ROOT / 'preview.html').read_text(), 'Rebuild preview.html after changing public assets')
        self.assertIn('window.NVTRA_PREVIEW_CONFIG=', html)
        self.assertNotIn('window.NVTRA_PREVIEW_CONFIG=', (ROOT / 'index.html').read_text())
        for name in ['studio', 'platform', 'cinematic']:
            self.assertNotIn(f'src="{name}.js"', html)
            self.assertNotIn(f'href="{name}.css"', html)
        self.assertNotIn('sqlite3.connect', html)
        self.assertNotIn('SMTP_PASSWORD=', html)
        self.assertIn('noindex,nofollow', html)
