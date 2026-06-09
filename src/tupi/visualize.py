"""Geração de visualizações da árvore sintática (parse tree) e da AST.

Dois formatos são produzidos, ambos por funções puras (recebem a árvore e
devolvem uma string):

* **DOT (Graphviz)** — ``lark_tree_to_dot`` / ``ast_to_dot``.
* **SVG autônomo** — ``lark_tree_to_svg`` / ``ast_to_svg``. Calcula o layout
  da árvore em Python e desenha o SVG diretamente, sem depender do binário do
  Graphviz nem de bibliotecas externas. É o formato usado pelo web app, pois
  permite zoom/arraste 100% offline.

Há ainda ``ast_to_text``, uma visão textual indentada.
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


# --------------------------------------------------------------------------- #
# SVG autônomo (layout calculado em Python, sem Graphviz)
# --------------------------------------------------------------------------- #
# Tanto a parse tree quanto a AST são árvores estritas (cada nó tem um pai), o
# que permite um layout simples: folhas posicionadas da esquerda para a direita
# e cada nó interno centralizado sobre seus filhos. Assim o web app consegue
# renderizar e dar zoom no grafo totalmente offline.

# Um "gnó" é um dicionário genérico que abstrai parse tree e AST:
#   {label, shape: "box"|"ellipse", fill, edge (rótulo da aresta com o pai),
#    children}. Os campos de layout (w, h, x, y) são preenchidos depois.

_CHAR_W = 7.6      # largura média de caractere (px) na fonte usada
_LINE_H = 16       # altura de uma linha de texto (px)
_PAD_X = 11        # respiro horizontal dentro do nó
_PAD_Y = 7         # respiro vertical dentro do nó
_MIN_W = 36        # largura mínima de um nó
_H_GAP = 26        # espaço horizontal entre nós irmãos
_V_GAP = 92        # distância vertical entre níveis (topo a topo)
_MARGIN = 24       # margem ao redor do desenho


def _svg_esc(texto: str) -> str:
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _gno_lark(no) -> dict:
    """Converte um nó da parse tree do Lark em um gnó genérico."""
    if isinstance(no, Tree):
        return {
            "label": str(no.data), "shape": "box", "fill": None, "edge": None,
            "children": [_gno_lark(c) for c in no.children if c is not None],
        }
    if isinstance(no, Token):
        tipo = _NOMES_TERMINAIS.get(no.type, no.type)
        valor = str(no).replace("\n", "\\n")
        return {
            "label": f"{tipo}\n{valor}", "shape": "ellipse",
            "fill": "#e8f0fe", "edge": None, "children": [],
        }
    return {"label": str(no), "shape": "ellipse", "fill": None,
            "edge": None, "children": []}


def _gno_ast(no, edge: str | None = None) -> dict:
    """Converte um nó da AST (dataclasses) em um gnó genérico."""
    if is_dataclass(no) and not isinstance(no, type):
        filhos = []
        for campo in fields(no):
            valor = getattr(no, campo.name)
            if valor is None:
                continue
            filhos.append(_gno_ast(valor, edge=campo.name))
        return {"label": type(no).__name__, "shape": "box", "fill": None,
                "edge": edge, "children": filhos}
    if isinstance(no, (list, tuple)):
        return {"label": "[ ]", "shape": "box", "fill": None, "edge": edge,
                "children": [_gno_ast(elem) for elem in no]}
    return {"label": str(no), "shape": "ellipse", "fill": "#fde8e8",
            "edge": edge, "children": []}


def _medir(gno: dict) -> None:
    linhas = str(gno["label"]).split("\n")
    largura = max((len(ln) for ln in linhas), default=1) * _CHAR_W + 2 * _PAD_X
    gno["w"] = max(largura, _MIN_W)
    gno["h"] = len(linhas) * _LINE_H + 2 * _PAD_Y
    for filho in gno["children"]:
        _medir(filho)


def _posicionar(gno: dict, prof: int, cursor: list[float]) -> None:
    gno["y"] = prof * _V_GAP
    if not gno["children"]:
        gno["x"] = cursor[0] + gno["w"] / 2
        cursor[0] = gno["x"] + gno["w"] / 2 + _H_GAP
        return
    for filho in gno["children"]:
        _posicionar(filho, prof + 1, cursor)
    gno["x"] = (gno["children"][0]["x"] + gno["children"][-1]["x"]) / 2
    # Garante que um nó interno largo não invada a subárvore irmã seguinte.
    direita = gno["x"] + gno["w"] / 2 + _H_GAP
    if direita > cursor[0]:
        cursor[0] = direita


def _render_svg(raiz: dict) -> str:
    _medir(raiz)
    _posicionar(raiz, 0, [0.0])

    nos: list[dict] = []
    arestas: list[tuple[dict, dict]] = []
    min_x, max_x, max_y = [1e18], [-1e18], [0.0]

    def coletar(no: dict, pai: dict | None) -> None:
        nos.append(no)
        min_x[0] = min(min_x[0], no["x"] - no["w"] / 2)
        max_x[0] = max(max_x[0], no["x"] + no["w"] / 2)
        max_y[0] = max(max_y[0], no["y"] + no["h"])
        if pai is not None:
            arestas.append((pai, no))
        for filho in no["children"]:
            coletar(filho, no)

    coletar(raiz, None)

    ox = _MARGIN - min_x[0]
    oy = _MARGIN
    largura = (max_x[0] - min_x[0]) + 2 * _MARGIN
    altura = max_y[0] + 2 * _MARGIN

    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura:.0f}" '
        f'height="{altura:.0f}" viewBox="0 0 {largura:.0f} {altura:.0f}" '
        'font-family="Helvetica, Arial, sans-serif">'
    ]

    # Arestas primeiro (ficam atrás dos nós).
    for pai, filho in arestas:
        x1, y1 = pai["x"] + ox, pai["y"] + oy + pai["h"]
        x2, y2 = filho["x"] + ox, filho["y"] + oy
        out.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            'stroke="#9aa0a6" stroke-width="1"/>'
        )
        if filho["edge"]:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            rotulo = _svg_esc(filho["edge"])
            largura_rot = len(filho["edge"]) * 6 + 6
            out.append(
                f'<rect x="{mx - largura_rot / 2:.1f}" y="{my - 8:.1f}" '
                f'width="{largura_rot:.1f}" height="14" fill="#ffffff" opacity="0.85"/>'
                f'<text x="{mx:.1f}" y="{my + 3:.1f}" font-size="10" fill="#5f6368" '
                f'text-anchor="middle">{rotulo}</text>'
            )

    # Nós.
    for no in nos:
        cx = no["x"] + ox
        top = no["y"] + oy
        w, h = no["w"], no["h"]
        fill = no["fill"] or "#ffffff"
        if no["shape"] == "ellipse":
            out.append(
                f'<ellipse cx="{cx:.1f}" cy="{top + h / 2:.1f}" rx="{w / 2:.1f}" '
                f'ry="{h / 2:.1f}" fill="{fill}" stroke="#5f6368" stroke-width="1"/>'
            )
        else:
            out.append(
                f'<rect x="{cx - w / 2:.1f}" y="{top:.1f}" width="{w:.1f}" '
                f'height="{h:.1f}" rx="7" ry="7" fill="{fill}" '
                'stroke="#5f6368" stroke-width="1"/>'
            )
        linhas = str(no["label"]).split("\n")
        y0 = top + (h - len(linhas) * _LINE_H) / 2 + _LINE_H * 0.74
        out.append(f'<text x="{cx:.1f}" y="{y0:.1f}" font-size="13" '
                   'text-anchor="middle" fill="#202124">')
        for i, ln in enumerate(linhas):
            dy = 0 if i == 0 else _LINE_H
            out.append(f'<tspan x="{cx:.1f}" dy="{dy}">{_svg_esc(ln)}</tspan>')
        out.append('</text>')

    out.append('</svg>')
    return "".join(out)


def lark_tree_to_svg(tree: Tree) -> str:
    """SVG autônomo (com layout próprio) da parse tree do Lark."""
    return _render_svg(_gno_lark(tree))


def ast_to_svg(node) -> str:
    """SVG autônomo (com layout próprio) da AST.

    Aceita tanto um nó dataclass quanto o invólucro ``Tree('start', [Program])``.
    """
    if isinstance(node, Tree):  # invólucro 'start'
        node = node.children[0]
    return _render_svg(_gno_ast(node))
