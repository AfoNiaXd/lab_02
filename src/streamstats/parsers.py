"""Потоковые парсеры CSV/JSONL и валидация события."""

import csv
import json
import logging

from datetime import datetime
from pathlib import Path

from .errors import EmptySourceError
from .errors import InvalidEventError
from .errors import InvalidLevelError
from .errors import InvalidTimestampError
from .errors import MissingColumnsError
from .errors import UnsupportedFormatError

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = {"timestamp", "level", "source", "message"}
ALLOWED_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def validate_event(obj):
    """Проверяет поля события и возвращает нормализованный dict."""
    if not isinstance(obj, dict):
        raise InvalidEventError(f"ожидался JSON-объект, получено {type(obj).__name__}")

    missing = REQUIRED_FIELDS - obj.keys()
    if missing:
        raise InvalidEventError(f"отсутствуют поля: {', '.join(sorted(missing))}")

    ts = obj["timestamp"]
    try:
        timestamp = datetime.fromisoformat(ts)
    except (TypeError, ValueError) as exc:
        raise InvalidTimestampError(f"некорректный timestamp: {ts!r}") from exc

    level = obj["level"]
    if not isinstance(level, str) or level not in ALLOWED_LEVELS:
        raise InvalidLevelError(f"недопустимый level: {level!r}")

    source = obj["source"]
    if not isinstance(source, str) or not source.strip():
        raise EmptySourceError(f"source должен быть непустой строкой, получено {source!r}")

    message = obj["message"]
    if not isinstance(message, str):
        raise InvalidEventError(f"message должен быть строкой, получено {type(message).__name__}")

    return {"timestamp": timestamp, "level": level, "source": source, "message": message}


def _handle_invalid(path, lineno, exc, skip_invalid):
    """Единая обработка битой строки: skip → WARNING + None, иначе — raise с file:line."""
    if skip_invalid:
        logger.warning("%s:%d: %s", path, lineno, exc)
        return
    raise InvalidEventError(f"{path}:{lineno}: {exc}") from exc


def iter_csv(path, skip_invalid=False):
    """Потоково читает CSV с заголовком и отдаёт события или None."""
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        if not f.readline().strip():
            return None
        f.seek(0)
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise UnsupportedFormatError(f"{path}: пустой CSV или нет заголовка")

        missing = REQUIRED_FIELDS - set(reader.fieldnames)
        if missing:
            raise MissingColumnsError(
                f"{path}: отсутствуют столбцы: {', '.join(sorted(missing))}"
            )

        for row in reader:
            lineno = reader.line_num
            try:
                yield validate_event(row)
            except InvalidEventError as exc:
                yield _handle_invalid(path, lineno, exc, skip_invalid)


def iter_jsonl(path, skip_invalid=False):
    """Потоково читает JSONL и отдаёт события или None для пропущенных строк."""
    with Path(path).open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                yield _handle_invalid(path, lineno, InvalidEventError("пустая строка"), skip_invalid)
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                yield _handle_invalid(path, lineno, InvalidEventError(f"невалидный JSON: {exc.msg}"), skip_invalid)
                continue
            try:
                yield validate_event(obj)
            except InvalidEventError as exc:
                yield _handle_invalid(path, lineno, exc, skip_invalid)


PARSERS = {"csv": iter_csv, "jsonl": iter_jsonl}


def iter_events(path, fmt, skip_invalid=False):
    """Возвращает итератор событий по файлу в заданном формате."""
    try:
        parser = PARSERS[fmt]
    except KeyError as exc:
        raise UnsupportedFormatError(f"неизвестный формат: {fmt!r}") from exc
    yield from parser(path, skip_invalid)
