"""Простые тесты на локальном HTTP-сервере."""
import io
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from demo_app import DemoHandler
from service_check import check_http, check_tcp


class CheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_http_ok(self):
        result = check_http(f"http://127.0.0.1:{self.port}/health")
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], 200)

    def test_http_error(self):
        result = check_http(f"http://127.0.0.1:{self.port}/fail")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], 503)

    def test_http_error_closes_response(self):
        stream = io.BytesIO(b"error body")
        error = HTTPError("http://127.0.0.1/fail", 503, "Unavailable", {}, stream)
        with patch("service_check.urlopen", side_effect=error):
            result = check_http("http://127.0.0.1/fail")
        self.assertEqual(result["status"], 503)
        self.assertTrue(stream.closed)

    def test_tcp_ok(self):
        result = check_tcp("127.0.0.1", self.port)
        self.assertTrue(result["ok"])

    def test_bad_url(self):
        with self.assertRaises(ValueError):
            check_http("127.0.0.1:8000")


if __name__ == "__main__":
    unittest.main()
