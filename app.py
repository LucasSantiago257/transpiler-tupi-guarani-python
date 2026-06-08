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


from tupi.lexer_parser import parse
from tupi.syntatic.transformer import transformer
from tupi.semantic.checker import SemanticChecker
from tupi.semantic.symbol_table import SemanticError
from tupi.codegen.emitter import CodeGenerator
from tupi.visualize import lark_tree_to_dot, ast_to_dot, ast_to_text

RAIZ = Path(__file__).parent
EXEMPLOS_DIR = RAIZ / "examples"


# --------------------------------------------------------------------------- #
# Pipeline de transpilação (reaproveita os módulos existentes do compilador)
# --------------------------------------------------------------------------- #
def transpilar(fonte: str) -> dict:
    """Roda as 4 etapas, capturando o erro na etapa em que ele ocorre."""
    res = {
        "parse_tree": None,
        "ast": None,
        "symtable": None,
        "codigo": None,
        "erro_etapa": None,   # "sintatica" | "ast" | "semantica" | "codegen"
        "erro_msg": None,
    }

    if not fonte.strip():
        res["erro_etapa"] = "sintatica"
        res["erro_msg"] = "Código-fonte vazio."
        return res

    # Etapa 1 — análise léxica + sintática
    try:
        res["parse_tree"] = parse(fonte)
    except Exception as e:
        res["erro_etapa"] = "sintatica"
        res["erro_msg"] = str(e)
        return res

    # Etapa 2 — construção da AST
    try:
        res["ast"] = transformer.transform(res["parse_tree"])
    except Exception as e:
        res["erro_etapa"] = "ast"
        res["erro_msg"] = str(e)
        return res

    # Etapa 3 — análise semântica
    try:
        checker = SemanticChecker()
        checker.check(res["ast"])
        res["symtable"] = checker.symtable
    except SemanticError as e:
        res["erro_etapa"] = "semantica"
        res["erro_msg"] = str(e)
        return res
    except Exception as e:
        res["erro_etapa"] = "semantica"
        res["erro_msg"] = str(e)
        return res

    # Etapa 4 — geração de código Python
    try:
        gerador = CodeGenerator(res["symtable"])
        res["codigo"] = gerador.generate(res["ast"])
    except Exception as e:
        res["erro_etapa"] = "codegen"
        res["erro_msg"] = str(e)

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


def _grafo_interativo(dot: str, altura: int = 650) -> None:
    """Grafo interativo (zoom com a roda do mouse, arraste para mover) via
    d3-graphviz. Requer internet (carrega bibliotecas de uma CDN)."""
    dot_json = json.dumps(dot)
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{ margin: 0; padding: 0; }}
  #grafo {{ width: 100%; height: {altura}px; overflow: hidden;
            border: 1px solid #e0e0e0; border-radius: 8px; background: #fff; }}
  #grafo svg {{ width: 100%; height: 100%; }}
  .dica {{ font-family: Helvetica, Arial, sans-serif; font-size: 12px;
           color: #666; margin: 2px 4px 6px; }}
</style>
<script src="https://unpkg.com/d3@5.16.0/dist/d3.min.js"></script>
<script src="https://unpkg.com/@hpcc-js/wasm@0.3.11/dist/index.min.js"></script>
<script src="https://unpkg.com/d3-graphviz@3.0.5/build/d3-graphviz.js"></script>
</head>
<body>
<div class="dica">🖱️ Role o mouse para ampliar/reduzir e arraste para mover.</div>
<div id="grafo"></div>
<script>
  var dot = {dot_json};
  d3.select("#grafo").graphviz().fit(true).zoom(true).renderDot(dot);
</script>
</body>
</html>
"""
    components.html(html, height=altura + 40, scrolling=False)


def _exibir_grafo(dot: str, chave: str) -> None:
    """Mostra o grafo no modo escolhido: interativo (CDN) ou estático (offline)."""
    modo = st.radio(
        "Modo de visualização",
        ["Interativo (zoom · requer internet)", "Estático (offline)"],
        horizontal=True,
        key=chave,
        help="Use o modo Estático se o grafo aparecer em branco (rede lenta/sem internet).",
    )
    if modo.startswith("Interativo"):
        _grafo_interativo(dot)
    else:
        st.caption("Passe o mouse sobre o grafo e use o botão de tela cheia (⤢) para ampliar.")
        st.graphviz_chart(dot, width="stretch")


# --------------------------------------------------------------------------- #
# Interface
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="Transpilador Tupi", page_icon="🌿", layout="wide")
st.title("🌿 Transpilador Tupi → Python")
st.caption("Visualização gráfica das etapas da compilação: análise sintática, AST, semântica e geração de código.")

exemplos = _listar_exemplos()

# Conteúdo inicial do editor: primeiro exemplo disponível.
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

aba_src, aba_parse, aba_ast, aba_sym, aba_py = st.tabs(
    ["Código-fonte", "Árvore Sintática", "AST", "Tabela de Símbolos", "Python"]
)

# --- Código-fonte ---------------------------------------------------------- #
with aba_src:
    st.code(st.session_state.fonte or "", language="text")

# --- Árvore Sintática (parse tree) ----------------------------------------- #
with aba_parse:
    if res["parse_tree"] is not None:
        _exibir_grafo(lark_tree_to_dot(res["parse_tree"]), chave="modo_arvore")
        with st.expander("Ver em texto (indentado)"):
            st.code(res["parse_tree"].pretty(), language="text")
    elif res["erro_etapa"] == "sintatica":
        st.error(f"Erro sintático:\n\n{res['erro_msg']}")
    else:
        _placeholder()

# --- AST ------------------------------------------------------------------- #
with aba_ast:
    if res["ast"] is not None:
        _exibir_grafo(ast_to_dot(res["ast"]), chave="modo_ast")
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
        st.error(f"Erro semântico:\n\n{res['erro_msg']}")
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
                    if proc.returncode != 0 and "EOFError" in (proc.stderr or ""):
                        # input() ficou sem dados: o programa pediu mais entradas
                        # do que foram fornecidas na caixa acima.
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
