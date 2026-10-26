"""Формирование и рендер отчёта (JSON, CSV)."""

import csv
import json

from .analysis import top_error_sources


def build_report(stats):
    """Формирует итоговый отчёт из накопленной статистики для записи в JSON."""
    first = stats["first_timestamp"]
    last = stats["last_timestamp"]
    return {
        "total": stats["total"],
        "skipped": stats["skipped"],
        "by_level": dict(stats["by_level"]),
        "by_source": dict(stats["by_source"]),
        "top_error_sources": [
            {"source": src, "count": cnt} for src, cnt in top_error_sources(stats)
        ],
        "first_timestamp": first.isoformat() if first else None,
        "last_timestamp": last.isoformat() if last else None,
    }


def write_json(report, fp):
    """Пишет отчёт в JSON-поток."""
    json.dump(report, fp, ensure_ascii=False, indent=2)
    fp.write("\n")


def write_csv(report, fp):
    """Пишет отчёт в CSV-поток."""
    writer = csv.writer(fp)
    writer.writerow(["section", "key", "value"])
    writer.writerow(["summary", "total", report["total"]])
    writer.writerow(["summary", "skipped", report["skipped"]])
    writer.writerow(["summary", "first_timestamp", report["first_timestamp"] or ""])
    writer.writerow(["summary", "last_timestamp", report["last_timestamp"] or ""])
    for level, cnt in sorted(report["by_level"].items()):
        writer.writerow(["by_level", level, cnt])
    for src, cnt in sorted(report["by_source"].items()):
        writer.writerow(["by_source", src, cnt])
    for rank, item in enumerate(report["top_error_sources"], start=1):
        writer.writerow([f"top_error_{rank}", item["source"], item["count"]])