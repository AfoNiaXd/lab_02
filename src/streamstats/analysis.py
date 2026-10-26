"""Аккумулятор статистики (dict) и агрегация событий."""

ERROR_LEVELS = {"ERROR", "CRITICAL"}


def new_stats():
    """Создаёт пустой словарь статистики со всеми ключами."""
    return {
        "total": 0,
        "skipped": 0,
        "by_level": {},
        "by_source": {},
        "errors_by_source": {},
        "first_timestamp": None,
        "last_timestamp": None,
    }


def analyze(event, stats):
    """Добавляет событие в статистику."""
    if event is None:
        stats["skipped"] += 1
        return stats

    stats["total"] += 1

    level = event["level"]
    source = event["source"]
    ts = event["timestamp"]

    stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
    stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

    if level in ERROR_LEVELS:
        stats["errors_by_source"][source] = stats["errors_by_source"].get(source, 0) + 1

    if stats["first_timestamp"] is None or ts < stats["first_timestamp"]:
        stats["first_timestamp"] = ts
    if stats["last_timestamp"] is None or ts > stats["last_timestamp"]:
        stats["last_timestamp"] = ts

    return stats


def top_error_sources(stats):
    """Возвращает top-5 источников по ERROR/CRITICAL, детерминированно по (-count, source)."""
    return sorted(stats["errors_by_source"].items(), key=lambda kv: (-kv[1], kv[0]))[:5]