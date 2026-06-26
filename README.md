# Transpilador Tupi-Guarani para Python (Tupi)

Transpilador de uma linguagem fonte esotérica com vocabulário **Tupi-Guarani** para **Python 3**.

> Implementação em Python utilizando o framework [Lark](https://github.com/lark-parser/lark) (LALR).

## Requisitos e Instalação

- Python ≥ 3.10

Clone esse repositório, crie um ambiente virtual e instale as dependências:

```bash
git clone https://github.com/LucasSantiago257/transpiler-tupi-guarani-python.git
python -m venv .venv 
.venv\Scripts\activate # No Windows
source .venv/bin/activate  # No Mac e Linux
cd transpiler-tupi-guarani-python
pip install -r requirements.txt
```

## Visualização Gráfica (Web App)

O projeto inclui um **visualizador gráfico** (web app em [Streamlit](https://streamlit.io/)) que mostra todas as etapas da transpilação lado a lado — código-fonte, árvore sintática, AST, tabela de símbolos e o Python gerado — e ainda permite **executar** o programa no navegador (com um campo de entrada para os comandos `monee`).

### Modo fácil (recomendado)

No **Windows**, basta dar **dois cliques em `run.bat`** — ele instala as dependências e abre o visualizador no navegador automaticamente. No **macOS/Linux**, rode `./run.sh`.

Ou, dentro do **VSCode**, abra `app.py` e clique no botão **▶ Run** — o próprio `app.py` se relança via Streamlit (não é preciso digitar `streamlit run`).

### Modo manual

```bash
pip install -r requirements.txt   # ou: pip install -e ".[web]"

# Inicie o visualizador (qualquer uma das opções):
streamlit run app.py
python app.py
python -m tupi.cli web
```

Na barra lateral você pode carregar um dos exemplos em `examples/` ou enviar o seu próprio arquivo `.tg`. O editor central re-transpila automaticamente a cada alteração.

Nas abas **Árvore Sintática** e **AST** o grafo é renderizado localmente (**offline**, não depende de internet). Para explorar:

- **Role a roda do mouse** para ampliar/reduzir e **arraste** para mover o grafo.
- Use o botão de **tela cheia (⤢)** no canto para uma visão maior.

Há também a opção *"Ver em texto (indentado)"*, uma visão textual da árvore que sempre funciona.

## Como Usar a CLI

Além do web app, o compilador inclui uma interface de linha de comando (`cli.py`) que processa todas as etapas: Parsing -> AST -> Semântica -> Codegen.

```bash
# Compilar um código tupi (gera o arquivo .py ao lado do original)
python -m tupi.cli compile examples/01_ola_mundo.tg

# Compilar para um diretório específico de saída
python -m tupi.cli compile examples/06_fibonacci.tg -o saida/meu_fibonacci.py

# Compilar e EXECUTAR o código Python gerado imediatamente
python -m tupi.cli compile examples/07_tpk.tg --run

# Exibir a árvore sintática (parse tree) gerada pelo Lark
python -m tupi.cli tree examples/01_ola_mundo.tg
```
Você também pode escrever seu próprio programa no formato .tg e utilizar o compilador tupi para transformá-lo em python!

## Exemplo de Programa Fonte

```
tekoha
  papy a, b, c.
  hei("Digite A").
  monee(a).
  hei("Digite B").
  monee(b).
  ramo (a < b) {
    c = a + b.
  } yro {
    c = a - b.
  }
  hei(c).
opa.
```

A saída esperada e a equivalência completa de tokens estão na documentação oficial do projeto em [`docs/linguagem.md`](docs/linguagem.md).

## Estrutura do Compilador

```
src/tupi/
  cli.py                 Interface de Linha de Comando Principal
  lexer_parser.py        Invólucro do Lexer/Parser do Lark
  grammar/tupi.lark      Regras LALR de parsing da linguagem
  syntatic/              Mapeamento de Árvores de Nós (AST e Transformer)
  semantic/              Tabela de Símbolos e Verificador Semântico (Checagem de Tipos)
  codegen/               Emissor de String Python nativo
  visualize.py           Geração de DOT (Graphviz) da parse tree e da AST
app.py                   Visualizador gráfico (web app Streamlit)
examples/
  *.tg                   7 programas escritos em Tupi
docs/
  linguagem.md           Especificação completa da linguagem Tupi
```

```
