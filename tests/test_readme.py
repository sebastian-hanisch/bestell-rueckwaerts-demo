"""README und App sagen dasselbe: geteilter Text, Testzahl, genannte Testnamen und Dateien, keine Platzhalter."""

import re
import subprocess
import sys
from pathlib import Path

from brw_texts import ASSUMPTIONS_MARKDOWN

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_the_shared_assumptions_text_is_in_the_readme_verbatim():
    assert ASSUMPTIONS_MARKDOWN.strip() in README


def test_the_test_count_in_the_readme_matches_the_suite():
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "tests", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True, timeout=300).stdout
    collected = int(re.search(r"(\d+) tests? collected", out).group(1))
    stated = int(re.search(r"\*\*(\d+) Tests\*\*", README).group(1))
    assert stated == collected


def test_every_test_name_the_readme_cites_exists():
    sources = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "tests").glob("test_*.py"))
    names = set(re.findall(r"`(test_[a-z0-9_]+)`", README))
    assert len(names) >= 15
    for name in names:
        assert re.search(rf"def {re.escape(name)}\b", sources), name


def test_every_file_the_readme_names_exists():
    for path in set(re.findall(r"`((?:tests|tools|data)/[A-Za-z0-9_./]+)`", README)) | set(re.findall(r"\| `([a-z_]+\.py)` \|", README)):
        assert (ROOT / path).exists(), path


def test_readme_has_no_open_placeholders():
    assert not [line for line in README.splitlines() if "TO" + "DO" in line]


def test_the_numbers_of_the_readme_table_use_the_decimal_comma():
    for line in README.splitlines():
        if line.startswith("| ") and "`test_" in line:
            assert not re.search(r"\d\.\d{1,2}\b", line), line      # kein Dezimalpunkt in den Tabellenzeilen (Tausenderpunkte stehen vor genau drei Ziffern)
