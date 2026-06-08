"""Geração de DOT (Graphviz) para visualizar a árvore sintática (parse tree)
e a AST do transpilador Tupi.

As funções são puras: recebem uma árvore e devolvem uma string no formato DOT,
renderizável por ``st.graphviz_chart`` (no navegador, sem binário do Graphviz).
"""
from __future__ import annotations

from dataclasses import is_dataclass, fields
from itertools import count

from lark import Tree, Token


def _escape(texto: str) -> str:
    """Escapa um rótulo para uso seguro dentro de aspas no DOT."""
    return (
        str(texto)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


# Nomes internos do Lark → nomes legíveis (alinhados com docs/linguagem.md).
_NOMES_TERMINAIS = {
    "ESCAPED_STRING": "STRING",
}


# --------------------------------------------------------------------------- #
# Árvore sintática (parse tree do Lark)
# --------------------------------------------------------------------------- #
def lark_tree_to_dot(tree: Tree) -> str:
    """Converte a parse tree crua do Lark em uma string DOT.

    Nós internos (regras) usam ``tree.data`` como rótulo; folhas (``Token``)
    mostram tipo e valor do terminal.
    """
    ids = count()
    linhas: list[str] = [
        "digraph parse_tree {",
        "  rankdir=TB;",
        '  node [shape=box, style=rounded, fontname="Helvetica"];',
    ]

    def visita(no) -> str:
        meu_id = f"n{next(ids)}"
        if isinstance(no, Tree):
            rotulo = str(no.data)
            linhas.append(f'  {meu_id} [label="{_escape(rotulo)}"];')
            for filho in no.children:
                if filho is None:
                    continue
                filho_id = visita(filho)
                linhas.append(f"  {meu_id} -> {filho_id};")
        elif isinstance(no, Token):
            tipo = _NOMES_TERMINAIS.get(no.type, no.type)
            rotulo = f"{tipo}\\n{no}"
            linhas.append(
                f'  {meu_id} [label="{_escape(rotulo)}", '
                'shape=ellipse, style=filled, fillcolor="#e8f0fe"];'
            )
        else:  # valor já transformado (str/int/...) — fallback defensivo
            linhas.append(
                f'  {meu_id} [label="{_escape(no)}", shape=ellipse];'
            )
        return meu_id

    visita(tree)
    linhas.append("}")
    return "\n".join(linhas)


# --------------------------------------------------------------------------- #
# AST (dataclasses de ast_nodes)
# --------------------------------------------------------------------------- #
def ast_to_dot(node) -> str:
    """Converte a AST (dataclasses) em uma string DOT.

    Aceita tanto um nó dataclass quanto o invólucro ``Tree('start', [Program])``
    devolvido pelo transformer — nesse caso desembrulha para o ``Program``.
    """
    if isinstance(node, Tree):  # invólucro 'start'
        node = node.children[0]

    ids = count()
    linhas: list[str] = [
        "digraph ast {",
        "  rankdir=TB;",
        '  node [shape=box, style=rounded, fontname="Helvetica"];',
    ]

    def folha(valor, *, cor: str | None = None) -> str:
        meu_id = f"n{next(ids)}"
        extra = f', style=filled, fillcolor="{cor}"' if cor else ""
        linhas.append(
            f'  {meu_id} [label="{_escape(valor)}", shape=ellipse{extra}];'
        )
        return meu_id

    def visita(no, *, rotulo_aresta: str | None = None) -> str:
        # Dataclass: nó interno com nome da classe.
        if is_dataclass(no) and not isinstance(no, type):
            meu_id = f"n{next(ids)}"
            linhas.append(
                f'  {meu_id} [label="{_escape(type(no).__name__)}"];'
            )
            for campo in fields(no):
                valor = getattr(no, campo.name)
                if valor is None:
                    continue
                filho_id = visita(valor, rotulo_aresta=campo.name)
                _aresta(meu_id, filho_id, campo.name)
            return meu_id

        # Lista (campos AsList: items / cmds / idents / decls).
        if isinstance(no, (list, tuple)):
            meu_id = f"n{next(ids)}"
            linhas.append(f'  {meu_id} [label="[ ]", shape=box];')
            for elem in no:
                filho_id = visita(elem)
                _aresta(meu_id, filho_id)
            return meu_id

        # Primitivo (str/int/float/bool) → folha colorida.
        return folha(no, cor="#fde8e8")

    def _aresta(origem: str, destino: str, rotulo: str | None = None) -> None:
        if rotulo:
            linhas.append(f'  {origem} -> {destino} [label="{_escape(rotulo)}", fontsize=10];')
        else:
            linhas.append(f"  {origem} -> {destino};")

    visita(node)
    linhas.append("}")
    return "\n".join(linhas)


def ast_to_text(node, _prof: int = 0) -> str:
    """Representação textual indentada da AST (sempre renderiza, sem rede).

    Útil como alternativa legível ao grafo, especialmente em árvores grandes.
    """
    if isinstance(node, Tree):  # invólucro 'start'
        node = node.children[0]

    linhas: list[str] = []

    def visita(no, prof: int) -> None:
        pad = "  " * prof
        if is_dataclass(no) and not isinstance(no, type):
            escalares: list[str] = []
            complexos: list[tuple[str, object]] = []
            for campo in fields(no):
                valor = getattr(no, campo.name)
                if valor is None:
                    continue
                if is_dataclass(valor) or isinstance(valor, (list, tuple)):
                    complexos.append((campo.name, valor))
                else:
                    escalares.append(f"{campo.name}={valor!r}")
            cabecalho = type(no).__name__
            if escalares:
                cabecalho += "  (" + ", ".join(escalares) + ")"
            linhas.append(pad + cabecalho)
            for nome_campo, valor in complexos:
                if isinstance(valor, (list, tuple)):
                    linhas.append("  " * (prof + 1) + nome_campo + ":")
                    for elem in valor:
                        visita(elem, prof + 2)
                else:
                    visita(valor, prof + 1)
        elif isinstance(no, (list, tuple)):
            for elem in no:
                visita(elem, prof)
        else:
            linhas.append(pad + repr(no))

    visita(node, _prof)
    return "\n".join(linhas)
