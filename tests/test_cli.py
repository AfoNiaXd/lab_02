import json

from streamstats.__main__ import main


def test_cli_multiple_files(tmp_path):
    """Тест нескольких файлов (объединение статистики)."""
    f1 = tmp_path / "server1.jsonl"
    f1.write_text(
        '{"timestamp":"2025-12-01T10:00:00","level":"INFO","source":"nginx","message":"200 OK"}\n',
        encoding="utf-8"
    )

    f2 = tmp_path / "server2.jsonl"
    f2.write_text(
        '{"timestamp":"2025-12-01T11:00:00","level":"ERROR","source":"nginx","message":"500 Error"}\n',
        encoding="utf-8"
    )

    out = tmp_path / "report.json"
    rc = main(["analyze", str(f1), str(f2), "--format", "jsonl", "--output", str(out)])

    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))

    assert report["total"] == 2
    assert report["by_source"] == {"nginx": 2}
    assert report["by_level"] == {"INFO": 1, "ERROR": 1}


def test_cli_stdout_and_skip_invalid(tmp_path, capsys):
    """Интеграционный тест: вывод в stdout и режим --skip-invalid."""
    f = tmp_path / "broken.jsonl"
    f.write_text(
        "broken line\n"
        '{"timestamp":"2025-12-01T10:00:00","level":"WARNING","source":"api","message":"slow"}\n',
        encoding="utf-8"
    )

    rc = main(["analyze", str(f), "--format", "jsonl", "--skip-invalid"])

    captured = capsys.readouterr()
    assert rc == 0

    report = json.loads(captured.out)
    assert report["skipped"] == 1
    assert report["total"] == 1


def test_cli_file_not_found(tmp_path, capsys):
    """Несуществующий файл должен давать понятную ошибку и код 2."""
    missing = tmp_path / "does_not_exist.jsonl"
    rc = main(["analyze", str(missing), "--format", "jsonl"])
    assert rc == 2
    captured = capsys.readouterr()
    assert "не найден" in captured.err.lower() or "not found" in captured.err.lower() or "No such file" in captured.err


def test_cli_empty_file_zero_report(tmp_path, capsys):
    """Пустой файл должен давать нулевой отчёт без ошибки."""
    f = tmp_path / "empty.jsonl"
    f.write_text("", encoding="utf-8")

    rc = main(["analyze", str(f), "--format", "jsonl"])
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["total"] == 0
    assert report["skipped"] == 0
    assert report["first_timestamp"] is None
    assert report["last_timestamp"] is None