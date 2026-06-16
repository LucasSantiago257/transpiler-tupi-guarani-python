# Etapa 1 do pipeline: LEXER + PARSER.
# Carrega grammar/tupi.lark e expõe parse()/parse_file(), que devolvem a
# parse tree crua do Lark (entrada da etapa 2, em syntatic/transformer.py).
from __future__ import annotations

from pathlib import Path
from lark import Lark, Tree

_GRAMMAR_PATH = Path(__file__).parent / "grammar" / "tupi.lark"


def _build_parser() -> Lark:
    grammar = _GRAMMAR_PATH.read_text(encoding="utf-8")
    # propagate_positions preenche line/column nos tokens e nós da árvore;
    # é o que permite reportar "linha X, coluna Y" nos erros léxicos e
    # sintáticos (CLI e web app leem esses atributos das exceptions do Lark).
    return Lark(grammar, parser="lalr", propagate_positions=True)


_PARSER: Lark | None = None


def get_parser() -> Lark:
    # Construir o parser LALR recompila a gramática inteira; cacheia-se a
    # instância num global do módulo para que chamadas repetidas (CLI, web
    # app, comandos "compile"/"tree") reaproveitem o mesmo parser.
    global _PARSER
    if _PARSER is None:
        _PARSER = _build_parser()
    return _PARSER


def parse(source: str) -> Tree:
    return get_parser().parse(source)


def parse_file(path: str | Path) -> Tree:
    return parse(Path(path).read_text(encoding="utf-8"))
