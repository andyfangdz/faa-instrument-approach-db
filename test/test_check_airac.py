from datetime import date
from pathlib import Path
import os
import subprocess
import sys

import pytest

from scripts.check_airac import check_schedule, is_airac_date


@pytest.mark.parametrize(
    "day, expected",
    [
        (date(2024, 1, 25), True),
        (date(2024, 2, 22), True),
        (date(2024, 2, 29), False),
        (date(2026, 8, 6), True),
        (date(2026, 9, 3), True),
        (date(2026, 9, 30), False),
        (date(2026, 10, 1), True),
        (date(2026, 10, 2), False),
    ],
)
def test_is_airac_date(day, expected):
    assert is_airac_date(day) is expected


def test_off_cycle_check_does_not_claim_publishing_succeeded():
    should_run, message = check_schedule(date(2026, 9, 30))
    assert not should_run
    assert "no data was published" in message
    assert "does not verify release freshness" in message


def test_effective_date_is_due():
    should_run, message = check_schedule(date(2026, 10, 1))
    assert should_run
    assert "scraping is due" in message


def test_manual_override():
    should_run, message = check_schedule(date(2026, 9, 30), force=True)
    assert should_run
    assert "Manual override" in message


def test_cli_writes_github_outputs(tmp_path):
    output = tmp_path / "output"
    summary = tmp_path / "summary"
    result = subprocess.run(
        [sys.executable, "scripts/check_airac.py", "--force", "true"],
        env={
            **os.environ,
            "GITHUB_OUTPUT": str(output),
            "GITHUB_STEP_SUMMARY": str(summary),
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_text() == "should_run=true\n"
    assert "Manual override" in summary.read_text()


def test_cli_invalid_input_fails_instead_of_skipping():
    result = subprocess.run(
        [sys.executable, "scripts/check_airac.py", "--force", "invalid"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_cli_output_failure_is_not_silently_skipped(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/check_airac.py"],
        env={**os.environ, "GITHUB_OUTPUT": str(tmp_path / "missing" / "output")},
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_workflows_share_supported_python_and_require_pdf_wheels():
    assert Path(".python-version").read_text().strip() == "3.12"
    for workflow in ("ci.yml", "scrape.yml"):
        contents = Path(".github/workflows", workflow).read_text()
        assert 'python-version-file: ".python-version"' in contents
        assert "--only-binary=pymupdf,pymupdfb" in contents
