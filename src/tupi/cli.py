import os
import sys
import subprocess
from pathlib import Path
import click

from tupi.lexer_parser import parse_file
from tupi.syntatic.transformer import transformer
from tupi.semantic.checker import SemanticChecker
from tupi.semantic.symbol_table import SemanticError
from tupi.codegen.emitter import CodeGenerator


@click.group()
def main():
    pass


@main.command()
@click.argument("arquivo", type=click.Path(exists=True))
@click.option("-o", "--output", default=None, help="Caminho do arquivo Python de saida.")
@click.option("--run", is_flag=True, help="Executa o codigo Python gerado apos a compilacao.")
def compile(arquivo, output, run):
    """Transpila um arquivo .tg para Python."""

    # --- Fase 1: Parse (Lexico + Sintatico) ---
    click.echo(f"[1/3] Analisando sintaticamente: {arquivo}")
    try:
        arvore_lark = parse_file(arquivo)
        arvore_ast = transformer.transform(arvore_lark)
    except Exception as e:
        click.echo(f"ERRO SINTATICO: {e}", err=True)
        sys.exit(1)

    # --- Fase 2: Analise Semantica ---
    click.echo("[2/3] Verificando semantica...")
    try:
        checker = SemanticChecker()
        checker.check(arvore_ast)
    except SemanticError as e:
        click.echo(f"{e}", err=True)
        sys.exit(1)

    # --- Fase 3: Geracao de Codigo ---
    click.echo("[3/3] Gerando codigo Python...")
    gerador = CodeGenerator(checker.symtable)
    codigo_python = gerador.generate(arvore_ast)

    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(codigo_python + "\n")
        click.echo(f"Arquivo gerado com sucesso: {output}")
    else:
        output = arquivo.rsplit(".", 1)[0] + ".py"
        with open(output, "w", encoding="utf-8") as f:
            f.write(codigo_python + "\n")
        click.echo(f"Arquivo gerado com sucesso: {output}")

    if run:
        click.echo(f"\n--- Executando {output} ---")
        result = subprocess.run([sys.executable, output])
        sys.exit(result.returncode)


@main.command()
@click.argument("arquivo", type=click.Path(exists=True))
def tree(arquivo):
    """Exibe a arvore sintatica (parse tree) de um arquivo .tg."""

    click.echo(f"Arvore sintatica de: {arquivo}\n")
    try:
        arvore_lark = parse_file(arquivo)
        click.echo(arvore_lark.pretty())
    except Exception as e:
        click.echo(f"ERRO SINTATICO: {e}", err=True)
        sys.exit(1)


@main.command()
def web():
    """Abre o visualizador grafico (web app Streamlit)."""

    app_path = Path(__file__).resolve().parents[2] / "app.py"
    if not app_path.exists():
        app_path = Path.cwd() / "app.py"
    if not app_path.exists():
        click.echo(f"ERRO: app.py nao encontrado em {app_path}", err=True)
        sys.exit(1)

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
    except FileNotFoundError:
        click.echo(
            "ERRO: Streamlit nao instalado. Rode: pip install -e \".[web]\"",
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
