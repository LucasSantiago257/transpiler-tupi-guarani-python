from __future__ import annotations

from pathlib import Path

import pytest

from tupi.lexer_parser import parse_file

SAMPLES_DIR = Path(__file__).parent / "samples"
SAMPLES = sorted(SAMPLES_DIR.glob("*.tg"))


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda p: p.name)
def test_sample_parses(sample: Path) -> None:
    tree = parse_file(sample)
    assert tree is not None
    assert tree.data == "start"
