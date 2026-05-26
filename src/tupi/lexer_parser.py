from __future__ import annotations

from pathlib import Path
from lark import Lark, Tree

_GRAMMAR_PATH = Path(__file__).parent / "grammar" / "tupi.lark"


def _build_parser() -> Lark:
    grammar = _GRAMMAR_PATH.read_text(encoding="utf-8")
    return Lark(grammar, parser="lalr", propagate_positions=True)


_PARSER: Lark | None = None


def get_parser() -> Lark:
    global _PARSER
    if _PARSER is None:
        _PARSER = _build_parser()
    return _PARSER


def parse(source: str) -> Tree:
    return get_parser().parse(source)


def parse_file(path: str | Path) -> Tree:
    return parse(Path(path).read_text(encoding="utf-8"))
