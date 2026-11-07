"""Mock-тесты: настоящая Jira не требуется."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jira_issue_reader import get_issue


class JiraReaderTests(unittest.TestCase):
    def test_invalid_key(self):
        with self.assertRaises(ValueError):
            get_issue("../token", "https://test.atlassian.net", "a@b.com", "fake")

    def test_requires_https(self):
        with self.assertRaises(ValueError):
            get_issue("DEMO-1", "http://test.atlassian.net", "a@b.com", "fake")

    def test_reads_fields(self):
        fake = {
            "key": "DEMO-1",
            "fields": {
                "summary": "Test issue",
                "status": {"name": "To Do"},
                "priority": {"name": "Medium"},
                "issuetype": {"name": "Task"},
            },
        }
        body = io.BytesIO(json.dumps(fake).encode("utf-8"))
        with patch("jira_issue_reader.build_opener") as builder:
            builder.return_value.open.return_value = body
            item = get_issue("DEMO-1", "https://test.atlassian.net",
                             "test@example.com", "not-real-token")
        self.assertEqual(item["summary"], "Test issue")
        self.assertEqual(item["status"], "To Do")
        self.assertEqual(item["priority"], "Medium")
        self.assertEqual(builder.return_value.open.call_count, 1)


if __name__ == "__main__":
    unittest.main()
