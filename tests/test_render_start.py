import unittest
from render_start import configure


class RenderStartup(unittest.TestCase):
    def test_render_origin_and_port(self):
        env = {'RENDER_EXTERNAL_URL': 'https://nvtra-example.onrender.com/', 'PORT': '12345', 'NVTRA_DATA_DIR': '/var/data/nvtra'}
        command = configure(env)
        self.assertEqual(env['NVTRA_PUBLIC_URL'], 'https://nvtra-example.onrender.com')
        self.assertIn('--listen=0.0.0.0:12345', command)
        self.assertEqual(command[-1], 'app:application')

    def test_custom_domain_overrides_render_origin(self):
        env = {'NVTRA_PUBLIC_URL': 'https://studio.example', 'RENDER_EXTERNAL_URL': 'https://nvtra-example.onrender.com', 'NVTRA_DATA_DIR': '/var/data/nvtra'}
        configure(env)
        self.assertEqual(env['NVTRA_PUBLIC_URL'], 'https://studio.example')

    def test_invalid_origins_fail_closed(self):
        for origin in ['', 'http://studio.example', 'https://studio.example/path', 'https://name:password@studio.example', 'https://studio.example?x=1']:
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                configure({'NVTRA_PUBLIC_URL': origin, 'NVTRA_DATA_DIR': '/var/data/nvtra'})

    def test_storage_and_port_required(self):
        with self.assertRaises(ValueError):
            configure({'RENDER_EXTERNAL_URL': 'https://studio.example'})
        for port in ['0', '65536', 'invalid']:
            with self.subTest(port=port), self.assertRaises(ValueError):
                configure({'RENDER_EXTERNAL_URL': 'https://studio.example', 'NVTRA_DATA_DIR': '/var/data/nvtra', 'PORT': port})
