# Transpilador Tupi-Guarani para Python (Tupi)

Transpilador de uma linguagem fonte esotérica com vocabulário **Tupi-Guarani** para **Python 3**.
A3 da disciplina *Teoria da Computação e Compiladores* (Prof. Eduardo Xavier).

> Implementação em Python utilizando o framework [Lark](https://github.com/lark-parser/lark) (LALR).

## Equipe Tupi Guarani - Autores

- Lucas Carvalho Santiago - 1272319058
- Guilherme Costa dos Santos - 12724135253
- João Manuel Da Silva Cunha - 12723127401
- Bruno Sales Fiaes Carneiro - 12723119186
- Bruno de Menezes Sales - 1272313072


## Requisitos e Instalação

- Python ≥ 3.10

Crie um ambiente virtual e instale as dependências:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Como Usar a CLI

O compilador inclui uma interface de linha de comando (`cli.py`) que processa todas as etapas: Parsing -> AST -> Semântica -> Codegen.

```bash
# Compilar um código tupi (gera o arquivo .py ao lado do original)
python -m tupi.cli compile examples/01_ola_mundo.tg

# Compilar para um diretório específico de saída
python -m tupi.cli compile examples/06_fibonacci.tg -o saida/meu_fibonacci.py

# Compilar e EXECUTAR o código Python gerado imediatamente
python -m tupi.cli compile examples/07_tpk.tg --run
```

## Exemplo de Programa Fonte

```
tekoha
  papy a, b, c.
  hei("Digite A").
  monee(a).
  hei("Digite B").
  monee(b).
  ojepe (a < b) {
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
examples/
  *.tg                   7 programas escritos em Tupi (incluindo Fibonacci e TPK)
docs/
  linguagem.md           Especificação completa da linguagem Tupi
```

## Agradecimentos

```
Agradecimentos à Documentação e criadores da library LARK e ao professor Eduardo Xavier.

```
