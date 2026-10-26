# Лабораторная работа № 2

- потоковый анализатор файлов журналов событий;
- подсчёт статистики и формирование JSON-отчёта.

Проект использует `src`-layout и предоставляет CLI-команду `streamstats`.

## Требования

- Python 3.10 или новее;
- `pytest` для запуска тестов;
- `ruff` для проверки стиля кода;
- `setuptools` для сборки/установки пакета.

## Установка

Скопировать директорию из Github:
```
git clone https://github.com/AfoNiaXd/laba_02
```
Написать в консоль:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

После установки CLI можно запускать так:

```bash
streamstats --help
```

Также доступен запуск без отдельной команды-обёртки:

```bash
python -m streamstats --help
```

> Команда `--help` выводит справку по доступным командам и параметрам.

## Использование

### Анализ файлов

Формат команды:

```text
python -m streamstats analyze INPUT [INPUT ...] --format csv|jsonl --output REPORT.json
```

Примеры:

```bash
python -m streamstats analyze events.csv --format csv
python -m streamstats analyze data.jsonl --format jsonl --output report.json
python -m streamstats analyze app1.jsonl app2.jsonl --format jsonl --output report.json
```

По умолчанию при обнаружении ошибочной строки программа останавливается и завершается с кодом `2`, указывая файл и номер строки.

### Режим пропуска ошибок

Если требуется обработать файл с повреждёнными строками, используется флаг `--skip-invalid`:

```bash
python -m streamstats analyze data.jsonl --format jsonl --skip-invalid
```

В этом режиме:
- повреждённые строки пропускаются;
- в лог (stderr) выводится предупреждение `WARNING`;
- количество пропущенных строк записывается в отчёт в поле `skipped`.

### Формат отчёта

В результате работы создаётся JSON-отчёт со следующей структурой:

```json
{
  "total": 4,
  "skipped": 1,
  "by_level": {"INFO": 2, "ERROR": 1, "CRITICAL": 1},
  "by_source": {"auth": 3, "billing": 1},
  "top_error_sources": [
    {"source": "auth", "count": 1},
    {"source": "billing", "count": 1}
  ],
  "first_timestamp": "2025-01-01T10:00:00",
  "last_timestamp": "2025-01-01T12:00:00"
}
```

## Структура проекта

```text
lab_02/
├── pyproject.toml
├── README.md
├── src/
│   └── streamstats/
│       ├── __init__.py
│       ├── __main__.py
│       ├── analysis.py
│       ├── errors.py
│       ├── parsers.py
│       └── report.py
└── tests/
    ├── test_analysis.py
    ├── test_cli.py
    └── test_parsers.py
```

- `pyproject.toml` — Системная информация, модули, метаданные, зависимости для разработки (pytest, ruff).
- `README.md` — Описание работы программы, инструкция по запуску и форматы данных.
- `__main__.py` — Основной вход и выход программы, настройка `argparse`, обработка кодов возврата и вызов парсеров.
- `parsers.py` — Содержит потоковые парсеры для форматов CSV и JSONL, а также логику обработки ошибочных строк.
- `analysis.py` — Содержит аккумулятор статистики и функции агрегации (подсчёт уровней, источников, времени).
- `report.py` — Содержит логику формирования итогового JSON-отчёта и его сериализации.
- `errors.py` — Содержит классы всех ошибок (базовое `StreamStatsError` и наследники).
- `test_parsers.py` — Тестирование парсеров CSV/JSONL, пустых файлов и повреждённых строк.
- `test_analysis.py` — Тестирование логики подсчёта статистики и поиска топ-5 источников ошибок.
- `test_cli.py` — Интеграционное тестирование чтения аргументов CLI и формирования отчёта.

## Тесты

Запуск из корня проекта:

```bash
python -m pytest
ruff check .
```