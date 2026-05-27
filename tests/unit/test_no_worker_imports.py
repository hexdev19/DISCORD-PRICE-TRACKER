"""Architecture rule guard: services must not import app.workers.*."""

from __future__ import annotations

import pathlib
import re

import pytest

FORBIDDEN_IN_SERVICES = re.compile(r"^\s*(from|import)\s+app\.workers")
FORBIDDEN_IN_SCRAPER = re.compile(
    r"^\s*(from|import)\s+app\.(services|repositories|models|bot|api|workers)"
)


@pytest.mark.parametrize(
    "package_dir,pattern",
    [
        ("app/services", FORBIDDEN_IN_SERVICES),
        ("app/scraper", FORBIDDEN_IN_SCRAPER),
    ],
)
def test_no_forbidden_imports(package_dir: str, pattern: re.Pattern[str]) -> None:
    offenders: list[str] = []
    for path in pathlib.Path(package_dir).rglob("*.py"):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                offenders.append(f"{path}:{lineno}: {line.strip()}")
    assert not offenders, "forbidden imports:\n" + "\n".join(offenders)
