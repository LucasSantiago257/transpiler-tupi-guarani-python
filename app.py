"""Visualizador gráfico do Transpilador Tupi → Python.

Aplicação Streamlit que mostra todas as etapas da transpilação
(análise sintática, AST, semântica e geração de código) e permite
executar o programa Python gerado no próprio navegador.

Execução:
    pip install -e ".[web]"
    streamlit run app.py
"""
from __future__ import annotations

import sys
import json
import subprocess
from pathlib import Path

# Garante que o pacote `tupi` (em src/) seja importável mesmo sem `pip install -e .`
_SRC = Path(__file__).parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st
import streamlit.components.v1 as components


def _sob_streamlit() -> bool:
    """True se o script está rodando dentro do runtime do Streamlit."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx(suppress_warning=True) is not None:
            return True
    except Exception:
        pass
    try:
        from streamlit.runtime import exists
        return exists()
    except Exception:
        return False


# "Easy-run": permite iniciar com `python app.py` (ou o botão ▶ Run do VSCode).
# Se não estivermos sob o runtime do Streamlit, o próprio script se relança
# via `streamlit run` e abre o navegador automaticamente.
if not _sob_streamlit():
    print("Iniciando o Transpilador Tupi (Streamlit)... aguarde o navegador abrir.")
    raise SystemExit(
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(Path(__file__).resolve())]
        ).returncode
    )


from lark.exceptions import UnexpectedCharacters, UnexpectedToken

from tupi.lexer_parser import parse
from tupi.syntatic.transformer import transformer
from tupi.semantic.checker import SemanticChecker
from tupi.semantic.symbol_table import SemanticError
from tupi.codegen.emitter import CodeGenerator
from tupi.visualize import lark_tree_to_svg, ast_to_svg, ast_to_text

RAIZ = Path(__file__).parent
EXEMPLOS_DIR = RAIZ / "examples"

# Palavras reservadas da linguagem (ver docs/linguagem.md, seção 1).
DICIONARIO = [
    {"Tupi": "tekoha",   "Python": "início do programa", "Significado": "lugar onde se vive"},
    {"Tupi": "opa",      "Python": "fim do programa",    "Significado": "acabar, terminar"},
    {"Tupi": "papy",     "Python": "int",                "Significado": "contagem, número"},
    {"Tupi": "papyvore", "Python": "float",              "Significado": "número fracionário"},
    {"Tupi": "nee",      "Python": "str",                "Significado": "palavra, fala"},
    {"Tupi": "anetepa",  "Python": "bool",               "Significado": "\"será verdade?\""},
    {"Tupi": "anete",    "Python": "True",               "Significado": "verdade"},
    {"Tupi": "japu",     "Python": "False",              "Significado": "mentira"},
    {"Tupi": "ramo",     "Python": "if",                 "Significado": "se, quando — condicional"},
    {"Tupi": "yro",      "Python": "else",               "Significado": "\"se não\" (negação da condição)"},
    {"Tupi": "aja",      "Python": "while",              "Significado": "durante, enquanto"},
    {"Tupi": "rupi",     "Python": "for",                "Significado": "por, através de"},
    {"Tupi": "japo",     "Python": "do…while (japo…aja)", "Significado": "fazer, realizar"},
    {"Tupi": "monee",    "Python": "input(...)",         "Significado": "ler (\"fazer falar\")"},
    {"Tupi": "hei",      "Python": "print(...)",         "Significado": "dizer, falar"},
]


# --------------------------------------------------------------------------- #
# Pipeline de transpilação (reaproveita os módulos existentes do compilador)
# --------------------------------------------------------------------------- #
def transpilar(fonte: str) -> dict:
    """Roda as 4 etapas, capturando e classificando o erro na etapa em que
    ele ocorre: Erro Léxico, Erro Sintático ou Erro Semântico."""
    res = {
        "parse_tree": None,
        "ast": None,
        "symtable": None,
        "codigo": None,
        "erro_etapa": None,   # "sintatica" | "ast" | "semantica" | "codegen"
        "erro_tipo": None,    # "Erro Léxico" | "Erro Sintático" | "Erro Semântico" | ...
        "erro_msg": None,
        "erro_linha": None,
        "erro_coluna": None,
    }

    def _falha(etapa: str, tipo: str, exc: Exception) -> dict:
        res["erro_etapa"] = etapa
        res["erro_tipo"] = tipo
        res["erro_msg"] = str(exc)
        res["erro_linha"] = getattr(exc, "line", None)
        res["erro_coluna"] = getattr(exc, "column", None)
        return res

    if not fonte.strip():
        res["erro_etapa"] = "sintatica"
        res["erro_tipo"] = "Erro Sintático"
        res["erro_msg"] = "Código-fonte vazio."
        return res

    # Etapa 1 — análise léxica + sintática. O Lark distingue os dois casos:
    # UnexpectedCharacters = caractere que nenhum token reconhece (léxico);
    # UnexpectedToken = token válido em posição inválida (sintático).
    try:
        res["parse_tree"] = parse(fonte)
    except UnexpectedCharacters as e:
        return _falha("sintatica", "Erro Léxico", e)
    except UnexpectedToken as e:
        return _falha("sintatica", "Erro Sintático", e)
    except Exception as e:
        return _falha("sintatica", "Erro Sintático", e)

    # Etapa 2 — construção da AST
    try:
        res["ast"] = transformer.transform(res["parse_tree"])
    except Exception as e:
        return _falha("ast", "Erro Sintático", e)

    # Etapa 3 — análise semântica
    try:
        checker = SemanticChecker()
        checker.check(res["ast"])
        res["symtable"] = checker.symtable
    except Exception as e:
        return _falha("semantica", "Erro Semântico", e)

    # Etapa 4 — geração de código Python
    try:
        gerador = CodeGenerator(res["symtable"])
        res["codigo"] = gerador.generate(res["ast"])
    except Exception as e:
        return _falha("codegen", "Erro de Geração de Código", e)

    return res


# --------------------------------------------------------------------------- #
# Callbacks da barra lateral (carregar exemplo / arquivo no editor)
# --------------------------------------------------------------------------- #
def _listar_exemplos() -> list[str]:
    if not EXEMPLOS_DIR.is_dir():
        return []
    return sorted(p.name for p in EXEMPLOS_DIR.glob("*.tg"))


def _carregar_exemplo() -> None:
    nome = st.session_state.get("exemplo_sel")
    if nome and nome != "—":
        st.session_state.fonte = (EXEMPLOS_DIR / nome).read_text(encoding="utf-8")


def _carregar_upload() -> None:
    arq = st.session_state.get("uploader")
    if arq is not None:
        st.session_state.fonte = arq.getvalue().decode("utf-8")


def _placeholder() -> None:
    st.info("Etapa não alcançada — corrija os erros das etapas anteriores.")


def _exibir_grafo(svg: str, altura: int = 620) -> None:
    """Mostra o grafo (SVG) num visor com zoom e deslocamento, 100% offline.

    O SVG é gerado em Python (ver ``tupi.visualize``); o zoom/arraste é feito
    aqui por um pequeno script embutido — não depende de internet, do binário
    do Graphviz nem de bibliotecas externas.
    """
    svg_json = json.dumps(svg)
    html = """
<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  html, body { margin: 0; padding: 0; font-family: Helvetica, Arial, sans-serif; }
  #wrap { position: relative; width: 100%; height: __ALT__px;
          border: 1px solid #e0e0e0; border-radius: 8px; background: #fff; overflow: hidden; }
  #vp { width: 100%; height: 100%; overflow: hidden; cursor: grab; }
  #vp.drag { cursor: grabbing; }
  #vp svg { position: absolute; top: 0; left: 0; transform-origin: 0 0; }
  #bar { position: absolute; top: 8px; right: 8px; display: flex; gap: 4px; z-index: 10; }
  #bar button { width: 30px; height: 30px; font-size: 16px; line-height: 1;
                border: 1px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; }
  #bar button:hover { background: #f1f3f4; }
  .hint { position: absolute; bottom: 6px; left: 8px; font-size: 11px; color: #80868b; }
</style></head><body>
<div id="wrap">
  <div id="bar">
    <button id="zin" title="Ampliar">+</button>
    <button id="zout" title="Reduzir">&minus;</button>
    <button id="zfit" title="Ajustar à tela">&#10530;</button>
  </div>
  <div id="vp"></div>
  <div class="hint">Role o mouse para zoom &middot; arraste para mover &middot; &#10530; ajusta</div>
</div>
<script>
  var vp = document.getElementById("vp");
  vp.innerHTML = __SVG__;
  var svg = vp.querySelector("svg");
  var W = svg.viewBox.baseVal.width, H = svg.viewBox.baseVal.height;
  svg.removeAttribute("width"); svg.removeAttribute("height");
  var k = 1, tx = 0, ty = 0;
  function apply() { svg.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + k + ")"; }
  function fit() {
    var r = vp.getBoundingClientRect();
    k = Math.min(r.width / W, r.height / H);
    if (!isFinite(k) || k <= 0) k = 1;
    if (k > 1) k = 1;                       // não amplia demais grafos pequenos
    tx = (r.width - W * k) / 2; ty = (r.height - H * k) / 2; apply();
  }
  function zoomAt(cx, cy, fator) {
    var nk = Math.max(0.05, Math.min(20, k * fator));
    tx = cx - (cx - tx) * (nk / k); ty = cy - (cy - ty) * (nk / k); k = nk; apply();
  }
  vp.addEventListener("wheel", function(e) {
    e.preventDefault();
    var r = vp.getBoundingClientRect();
    zoomAt(e.clientX - r.left, e.clientY - r.top, e.deltaY < 0 ? 1.12 : 1 / 1.12);
  }, { passive: false });
  var drag = false, lx = 0, ly = 0;
  vp.addEventListener("mousedown", function(e) { drag = true; lx = e.clientX; ly = e.clientY; vp.classList.add("drag"); });
  window.addEventListener("mousemove", function(e) {
    if (!drag) return;
    tx += e.clientX - lx; ty += e.clientY - ly; lx = e.clientX; ly = e.clientY; apply();
  });
  window.addEventListener("mouseup", function() { drag = false; vp.classList.remove("drag"); });
  document.getElementById("zin").onclick = function() { var r = vp.getBoundingClientRect(); zoomAt(r.width / 2, r.height / 2, 1.25); };
  document.getElementById("zout").onclick = function() { var r = vp.getBoundingClientRect(); zoomAt(r.width / 2, r.height / 2, 1 / 1.25); };
  document.getElementById("zfit").onclick = fit;
  fit();
</script></body></html>
"""
    html = html.replace("__ALT__", str(altura)).replace("__SVG__", svg_json)
    components.html(html, height=altura + 4, scrolling=False)


# --------------------------------------------------------------------------- #
# Interface
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="Transpilador Tupi", page_icon="🌿", layout="wide")
st.title("🌿 Transpilador Tupi → Python")
st.caption("Visualização gráfica das etapas da compilação: análise sintática, AST, semântica e geração de código.")

exemplos = _listar_exemplos()

if "fonte" not in st.session_state:
    st.session_state.fonte = (
        (EXEMPLOS_DIR / exemplos[0]).read_text(encoding="utf-8") if exemplos else ""
    )

with st.sidebar:
    st.header("Entrada")
    st.selectbox(
        "Exemplos",
        ["—"] + exemplos,
        key="exemplo_sel",
        on_change=_carregar_exemplo,
        help="Selecione um programa de exemplo para carregar no editor.",
    )
    st.file_uploader(
        "Enviar arquivo .tg",
        type=["tg"],
        key="uploader",
        on_change=_carregar_upload,
    )
    with st.expander("📖 Dicionário (palavras reservadas)"):
        st.dataframe(DICIONARIO, hide_index=True, width="stretch")
    st.markdown("---")
    st.caption("Edite o código no editor e as etapas são atualizadas automaticamente.")

st.subheader("Editor")
fonte = st.text_area(
    "Código-fonte (.tg)",
    key="fonte",
    height=280,
    label_visibility="collapsed",
)

res = transpilar(st.session_state.fonte)

# Banner de erro classificado (Léxico / Sintático / Semântico) sob o editor.
if res["erro_etapa"]:
    local = ""
    if res["erro_linha"]:
        local = f" — linha {res['erro_linha']}, coluna {res['erro_coluna']}"
    st.error(f"**{res['erro_tipo']}**{local}\n\n{res['erro_msg']}")

aba_py, aba_src, aba_parse, aba_ast, aba_sym = st.tabs(
    ["Python", "Código-fonte", "Árvore Sintática", "AST", "Tabela de Símbolos"]
)

# --- Código-fonte ---------------------------------------------------------- #
with aba_src:
    st.code(st.session_state.fonte or "", language="text")

# --- Árvore Sintática (parse tree) ----------------------------------------- #
with aba_parse:
    if res["parse_tree"] is not None:
        _exibir_grafo(lark_tree_to_svg(res["parse_tree"]))
        with st.expander("Ver em texto (indentado)"):
            st.code(res["parse_tree"].pretty(), language="text")
    elif res["erro_etapa"] == "sintatica":
        st.error(f"{res['erro_tipo']}:\n\n{res['erro_msg']}")
    else:
        _placeholder()

# --- AST ------------------------------------------------------------------- #
with aba_ast:
    if res["ast"] is not None:
        _exibir_grafo(ast_to_svg(res["ast"]))
        with st.expander("Ver em texto (indentado)"):
            st.code(ast_to_text(res["ast"]), language="text")
    elif res["erro_etapa"] == "ast":
        st.error(f"Erro na construção da AST:\n\n{res['erro_msg']}")
    else:
        _placeholder()

# --- Tabela de Símbolos ---------------------------------------------------- #
with aba_sym:
    if res["symtable"] is not None:
        simbolos = res["symtable"]._symbols
        if simbolos:
            linhas = [
                {
                    "nome": s.name,
                    "tipo Tupi": s.tupi_type,
                    "tipo Python": s.python_type,
                }
                for s in simbolos.values()
            ]
            st.dataframe(linhas, width='stretch', hide_index=True)
        else:
            st.info("Nenhuma variável declarada.")
    elif res["erro_etapa"] == "semantica":
        st.error(f"{res['erro_tipo']}:\n\n{res['erro_msg']}")
    else:
        _placeholder()

# --- Python gerado + execução ---------------------------------------------- #
with aba_py:
    if res["codigo"] is not None:
        col_code, col_run = st.columns(2)

        with col_code:
            st.subheader("Código gerado")
            st.code(res["codigo"], language="python")
            st.download_button(
                "Baixar .py",
                data=res["codigo"] + "\n",
                file_name="programa.py",
                mime="text/x-python",
            )

        with col_run:
            st.subheader("Executar")
            st.caption(
                "Forneça **uma entrada por linha**, na ordem em que os comandos "
                "`monee` são executados. Laços que leem dados precisam de uma linha "
                "para cada repetição (ex.: ler `n` e depois `n` valores)."
            )
            stdin_txt = st.text_area(
                "Entrada (stdin) — um valor por linha",
                key="stdin",
                height=120,
                help="Valores lidos pelos comandos 'monee' (input), na ordem.",
            )
            if st.button("Executar", type="primary"):
                try:
                    proc = subprocess.run(
                        [sys.executable, "-c", res["codigo"]],
                        input=stdin_txt,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if proc.stdout:
                        st.markdown("**Saída:**")
                        st.code(proc.stdout, language="text")
                    # EOFError = o programa pediu mais entradas do que foram fornecidas.
                    if proc.returncode != 0 and "EOFError" in (proc.stderr or ""):
                        st.warning(
                            "⚠️ O programa pediu **mais entradas do que você forneceu**. "
                            "Adicione mais valores na caixa **Entrada (stdin)** acima "
                            "(uma por linha) e execute novamente. "
                            "Dica: laços que leem dados consomem uma linha por repetição."
                        )
                        with st.expander("Detalhes técnicos"):
                            st.code(proc.stderr, language="text")
                    elif proc.stderr:
                        st.markdown("**Erro de execução:**")
                        st.code(proc.stderr, language="text")
                    if not proc.stdout and not proc.stderr:
                        st.info("Programa executado sem saída.")
                except subprocess.TimeoutExpired:
                    st.error("Tempo de execução excedido (10s) — possível laço infinito.")
    elif res["erro_etapa"] == "codegen":
        st.error(f"Erro na geração de código:\n\n{res['erro_msg']}")
    else:
        _placeholder()
