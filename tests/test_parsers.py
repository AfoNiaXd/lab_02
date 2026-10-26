import pytest

from streamstats.errors import InvalidEventError
from streamstats.parsers import iter_csv
from streamstats.parsers import iter_jsonl


def test_csv_valid(tmp_path):
    """Чтение валидного CSV."""
    f = tmp_path / "test.csv"
    f.write_text(
        "timestamp,level,source,message\n"
        "2025-05-10T10:00:00,ERROR,payment,failed\n"
        "2025-05-10T11:00:00,INFO,auth,login\n",
        encoding="utf-8"
    )
    events = list(iter_csv(f))
    assert len(events) == 2
    assert events[0]["source"] == "payment"
    assert events[1]["level"] == "INFO"


def test_jsonl_valid(tmp_path):
    """Чтение валидного JSONL."""
    f = tmp_path / "test.jsonl"
    f.write_text(
        '{"timestamp":"2025-05-10T10:00:00","level":"DEBUG","source":"db","message":"query"}\n'
        '{"timestamp":"2025-05-10T11:00:00","level":"CRITICAL","source":"db","message":"disk full"}\n',
        encoding="utf-8"
    )
    events = list(iter_jsonl(f))
    assert len(events) == 2
    assert events[1]["level"] == "CRITICAL"


def test_unicode(tmp_path):
    """Тест на Unicode символы в файле."""
    f = tmp_path / "uni.jsonl"
    f.write_text(
        '{"timestamp":"2025-05-10T10:00:00","level":"INFO","source":"Сервер-А","message":"Ошибка: сбой"}\n',
        encoding="utf-8"
    )
    events = list(iter_jsonl(f))
    assert events[0]["source"] == "Сервер-А"
    assert "сбой" in events[0]["message"]


def test_empty_files(tmp_path):
    """Тест пустых файлов."""
    empty_jsonl = tmp_path / "empty.jsonl"
    empty_jsonl.write_text("", encoding="utf-8")
    assert list(iter_jsonl(empty_jsonl)) == []

    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("timestamp,level,source,message\n", encoding="utf-8")
    assert list(iter_csv(empty_csv)) == []


def test_corrupted_row_strict_mode(tmp_path):
    """Тест поврежденной строки в строгом режиме (должно выбросить ошибку)."""
    f = tmp_path / "bad.csv"
    f.write_text(
        "timestamp,level,source,message\n"
        "2025-05-10T10:00:00,SUPER_ERROR,app,crash\n",
        encoding="utf-8"
    )

    with pytest.raises(InvalidEventError) as exc_info:
        list(iter_csv(f, skip_invalid=False))

    # Проверяем, что в ошибке есть имя файла и номер строки
    assert "bad.csv:2" in str(exc_info.value)


def test_corrupted_row_skip_mode(tmp_path):
    """Тест поврежденной строки в режиме --skip-invalid."""
    f = tmp_path / "bad.jsonl"
    f.write_text(
        "это не JSON\n"
        '{"timestamp":"2025-05-10T10:00:00","level":"INFO","source":"app","message":"ok"}\n',
        encoding="utf-8"
    )

    events = list(iter_jsonl(f, skip_invalid=True))
    assert len(events) == 2
    assert events[0] is None
    assert events[1]["level"] == "INFO"


def test_empty_csv_zero_bytes(tmp_path):
    """Полностью пустой CSV (0 байт) должен давать пустой итератор без ошибки."""
    f = tmp_path / "empty.csv"
    f.write_text("", encoding="utf-8")
    assert list(iter_csv(f)) == []


def test_invalid_timestamp_reports_line(tmp_path):
    """Невалидный timestamp должен указывать файл и номер строки."""
    f = tmp_path / "bad_ts.jsonl"
    f.write_text(
        '{"timestamp":"не-дата","level":"INFO","source":"app","message":"ok"}\n',
        encoding="utf-8",
    )
    with pytest.raises(InvalidEventError) as exc_info:
        list(iter_jsonl(f, skip_invalid=False))
    msg = str(exc_info.value)
    assert "bad_ts.jsonl:1" in msg
    assert "timestamp" in msg.lower() or "некорректный" in msg.lower()


def test_csv_and_jsonl_same_stats(tmp_path):
    """Одинаковые данные в CSV и JSONL должны давать одинаковую статистику."""
    csv_file = tmp_path / "data.csv"
    jsonl_file = tmp_path / "data.jsonl"

    csv_file.write_text(
        "timestamp,level,source,message\n"
        "2025-05-10T10:00:00,ERROR,payment,failed\n"
        "2025-05-10T11:00:00,INFO,auth,login\n",
        encoding="utf-8",
    )
    jsonl_file.write_text(
        '{"timestamp":"2025-05-10T10:00:00","level":"ERROR","source":"payment","message":"failed"}\n'
        '{"timestamp":"2025-05-10T11:00:00","level":"INFO","source":"auth","message":"login"}\n',
        encoding="utf-8",
    )