"""CLI: argparse, оркестрация, коды возврата, настройка логирования."""

import argparse
import logging
import sys

from pathlib import Path

from .analysis import analyze
from .analysis import new_stats
from .errors import InvalidEventError
from .errors import StreamStatsError
from .parsers import iter_events
from .report import build_report
from .report import write_json

logger = logging.getLogger("streamstats")


def configure_logging():
    """Настраивает logging: уровень WARNING, вывод в stderr."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s",
                        stream=sys.stderr, force=True)


def build_parser():
    """Создаёт argparse-парсер с хелпом."""

    analyze_help = """
Параметры команды analyze:
  INPUT                 один или несколько входных файлов
  --format {csv,jsonl}  формат входных файлов (обязателен)
  --output REPORT       путь к JSON-отчёту (по умолчанию — stdout)
  --skip-invalid        пропускать битые строки, писать WARNING в лог, считать skipped

Примеры:
  python -m streamstats analyze events.csv --format csv
  python -m streamstats analyze data.jsonl --format jsonl --output report.json
"""

    parser = argparse.ArgumentParser(
        prog="streamstats",
        description="Потоковый анализатор журналов событий (CSV/JSONL).",
        epilog=analyze_help,
        formatter_class=argparse.RawDescriptionHelpFormatter  # Чтобы сохранить переносы строк
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
        metavar="COMMAND",
        title="команды",
    )

    p = sub.add_parser(
        "analyze",
        help="Анализ файлов и построение JSON-отчёта (подробности см. ниже)",
    )

    p.add_argument("inputs", nargs="+", type=Path, metavar="INPUT")
    p.add_argument("--format", choices=["csv", "jsonl"], required=True)
    p.add_argument("--output", type=Path, default=None, metavar="REPORT")
    p.add_argument("--skip-invalid", action="store_true")
    p.set_defaults(func=run_analyze)

    return parser


def run_analyze(args):
    """Обрабатывает все входные файлы и пишет отчёт."""
    stats = new_stats()
    for path in args.inputs:
        if not path.exists():
            raise StreamStatsError(f"файл не найден: {path}")
        if not path.is_file():
            raise StreamStatsError(f"не является файлом: {path}")
        for event in iter_events(path, args.format, args.skip_invalid):
            stats = analyze(event, stats)
    report = build_report(stats)
    if args.output:
        with args.output.open("w", encoding="utf-8") as fp:
            write_json(report, fp)
    else:
        write_json(report, sys.stdout)
    return 0


def main(argv=None):
    """Точка входа CLI"""
    args = build_parser().parse_args(argv)
    configure_logging()
    try:
        return args.func(args)
    except InvalidEventError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except StreamStatsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:          # на всякий случай
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
