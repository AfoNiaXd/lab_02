from datetime import datetime

import pytest

from streamstats.analysis import analyze
from streamstats.analysis import new_stats


def event(level="INFO", source="auth", timestamp="2025-05-10T12:00:00"):
    """Хелпер для создания тестового события."""
    return {
        "timestamp": datetime.fromisoformat(timestamp),
        "level": level,
        "source": source,
        "message": "Тестовое сообщение",
    }


def test_one_event():
    stats = new_stats()
    stats = analyze(event(), stats)

    assert stats["total"] == 1
    assert stats["by_level"]["INFO"] == 1
    assert stats["by_source"] == {"auth": 1}
    assert stats["first_timestamp"] == datetime(2025, 5, 10, 12, 0, 0)
    assert stats["last_timestamp"] == datetime(2025, 5, 10, 12, 0, 0)


@pytest.mark.parametrize(
    "level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
)
def test_levels(level):
    stats = new_stats()
    stats = analyze(event(level), stats)

    assert stats["by_level"][level] == 1
    if level in ["ERROR", "CRITICAL"]:
        assert stats["errors_by_source"] == {"auth": 1}
    else:
        assert stats["errors_by_source"] == {}


def test_first_and_last_timestamp():
    stats = new_stats()
    for timestamp in ["2025-05-10T20:00:00", "2025-05-10T08:00:00", "2025-05-10T15:00:00"]:
        analyze(event(timestamp=timestamp), stats)

    assert stats["first_timestamp"] == datetime(2025, 5, 10, 8, 0, 0)
    assert stats["last_timestamp"] == datetime(2025, 5, 10, 20, 0, 0)


def test_sources_and_errors():
    stats = new_stats()
    items = [
        event(level="ERROR", source="billing"),
        event(level="CRITICAL", source="billing"),
        event(level="WARNING", source="auth"),
        event(level="INFO", source="db")
    ]

    for item in items:
        analyze(item, stats)

    assert stats["total"] == 4
    assert stats["by_source"] == {"billing": 2, "auth": 1, "db": 1}
    assert stats["errors_by_source"] == {"billing": 2}


def test_skipped_events():
    stats = new_stats()
    stats = analyze(None, stats)
    assert stats["skipped"] == 1
    assert stats["total"] == 0