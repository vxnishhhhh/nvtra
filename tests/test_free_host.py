import unittest
from scripts.setup_free_host import wsgi_source


class FreeHost(unittest.TestCase):
    def test_free_domain_and_storage(self):
        source = wsgi_source('nvtra-example.pythonanywhere.com', root='/home/example/nvtra', data='/home/example/private/nvtra')
        compile(source, '<wsgi>', 'exec')
        self.assertIn('https://nvtra-example.pythonanywhere.com', source)
        self.assertIn('/home/example/private/nvtra', source)
        self.assertIn('from app import application', source)
        self.assertNotIn('waitress', source)

    def test_eu_domain(self):
        self.assertIn('https://example.eu.pythonanywhere.com', wsgi_source('example.eu.pythonanywhere.com'))

    def test_reject_non_free_domain_or_injection(self):
        for domain in ['http://example.pythonanywhere.com', 'example.com', 'example.pythonanywhere.com/path', 'example.pythonanywhere.com\nmalicious', 'example.pythonanywhere.com.evil.test']:
            with self.subTest(domain=domain), self.assertRaises(ValueError):
                wsgi_source(domain)

    def test_reject_public_storage(self):
        with self.assertRaises(ValueError):
            wsgi_source('example.pythonanywhere.com',root='/tmp/example/nvtra',data='/tmp/example/nvtra/.data')
