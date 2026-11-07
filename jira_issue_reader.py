"""Read-only просмотр одного тикета Jira Cloud REST API v3.

Нужны JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN в переменных окружения.
Только GET-запросы. Токены и переписка с клиентами не сохраняются.
"""
import argparse
import base64
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen


def get_issue(key, base_url, email, api_token):
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*-[1-9][0-9]*", key):
        raise ValueError("Ожидается ключ типа DEMO-1")
    base_url = base_url.strip().rstrip("/")
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Для Jira Cloud нужен HTTPS URL")
    if not email or not api_token:
        raise ValueError("Нужны JIRA_EMAIL и JIRA_API_TOKEN")

    credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
    endpoint = base_url + "/rest/api/3/issue/" + quote(key, safe="")
    endpoint += "?fields=summary,status,priority,issuetype"
    request = Request(endpoint, headers={
        "Authorization": "Basic " + credentials,
        "Accept": "application/json",
        "User-Agent": "it-support-study/0.1",
    })
    with urlopen(request, timeout=10) as response:
        data = json.load(response)
    fields = data.get("fields") or {}
    return {
        "key": data.get("key", key),
        "summary": fields.get("summary"),
        "status": (fields.get("status") or {}).get("name"),
        "priority": (fields.get("priority") or {}).get("name"),
        "type": (fields.get("issuetype") or {}).get("name"),
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only Jira issue reader")
    parser.add_argument("key", help="Например, DEMO-1")
    args = parser.parse_args()
    try:
        result = get_issue(
            args.key,
            os.getenv("JIRA_URL", ""),
            os.getenv("JIRA_EMAIL", ""),
            os.getenv("JIRA_API_TOKEN", ""),
        )
    except (ValueError, HTTPError, URLError, OSError) as exc:
        # Ошибка без публикации токенов и тела ответа сервера.
        print(f"Не удалось получить задачу: {type(exc).__name__}")
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
