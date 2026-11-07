# Jira Cloud API — отдельная учебная интеграция

В основном проекте используются **учебные текстовые тикеты**. Этот скрипт показывает, как прочитать *настоящую* задачу из своей тестовой Jira Cloud через REST API v3. Он **ничего не меняет** в Jira.

## Что потребуется

1. Собственный тестовый Jira Cloud проект, например DEMO.
2. Учебный тикет, например DEMO-1.
3. Email своей учётной записи Atlassian и API token, выданный для Jira (хранить как пароль).

В Linux / WSL установить переменные окружения:

~~~bash
export JIRA_URL="https://your-site.atlassian.net"
export JIRA_EMAIL="you@example.com"
read -rs JIRA_API_TOKEN
export JIRA_API_TOKEN
python jira_issue_reader.py DEMO-1
unset JIRA_API_TOKEN
~~~

На Windows PowerShell переменные задаются через $env:JIRA_URL, $env:JIRA_EMAIL и $env:JIRA_API_TOKEN. Не сохранять токен в публичных shell history, скриншотах и GitHub Actions.

## Что вернётся

JSON с ключом, темой, типом, статусом и приоритетом задачи. Нет создания, редактирования и удаления тикетов.

## Проверить код без Jira

~~~bash
python -m unittest discover -s tests -v
~~~

Тесты используют mock, а не живое соединение с Atlassian. Работа с реальной Jira API до подключения тестовой среды **не подтверждена**.

Скрипт — учебный пример. Для корпоративной Jira требуется согласовать доступ и правила безопасности.
