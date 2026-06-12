# Linguagem Tupi — Especificação

Linguagem de programação fonte deste transpilador. Tem vocabulário inspirado no **Tupi-Guarani** e é convertida para **Python 3** pelo nosso compilador (`tupi`).

---

## 1. Vocabulário (palavras reservadas)

| Palavra (código) | Grafia autêntica | Significado em Tupi-Guarani | Equivalente Python |
|------------|------------|------------|------------|
| `tekoha` | tekoha | lugar onde se vive | Início do script principal |
| `opa` | opa | acabar, terminar | Fim do script principal |
| `papy` | papy | contagem, número | `int` |
| `papyvore` | papy + vore | número + parte/fração → número fracionário | `float` |
| `nee` | ñe'ẽ | palavra, fala | `str` |
| `anetepa` | añetepa | "será verdade?" | `bool` |
| `anete` | añete | verdade | `True` |
| `japu` | japu | mentira | `False` |
| `ramo` | ramo (rõ) | se, quando (condicional) | `if` |
| `yro` | ỹrõ | ỹ (não) + rõ (se) = "se não" | `else` |
| `aja` | aja | durante, enquanto | `while` |
| `rupi` | rupi | por, através de | `for` |
| `japo` | japo | fazer, realizar | `while True` com quebra |
| `monee` | moñe'ẽ | ler (mo + ñe'ẽ = "fazer falar") | `input(...)` |
| `hei` | he'i | dizer, falar | `print(...)` |

### Operadores e pontuação
- Aritméticos: `+`, `-`, `*`, `/`
- Relacionais: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Atribuição: `=`
- Terminador de comando: `.`
- Delimitadores de bloco: `{` `}`
- Delimitadores de expressão / argumento: `(` `)`
- Separador de lista: `,`

### Comentários
- De linha: `# até o fim da linha`

> As grafias autênticas e os significados desta seção foram revisados com base
> nas referências em [`fontes_dicionario.md`](fontes_dicionario.md) (dicionário
> Tupi de Gonçalves Dias, Wikibooks de gramática Guarani e o *Tesoro de la
> Lengua Guaraní* de Montoya).

---

## 2. Estrutura geral de um programa

```
tekoha
  <declarações>
  <comandos>
opa.
```

Toda declaração e todo comando terminam com `.` — exceto blocos delimitados por `{ }`, que não levam ponto final.

---

## 3. Declarações de variáveis

```
<tipo> Id (, Id)* .
```

Exemplos:

```
papy       a, b, c.
papyvore   raio.
nee        nome.
anetepa    ativo.
```

Regras semânticas:
- **Não pode redeclarar** identificador no mesmo escopo.
- **Toda variável deve ser declarada antes de qualquer uso** (em expressão, atribuição, leitura ou escrita).
- O **tipo** declarado fixa as operações permitidas.

---

## 4. Comandos

### 4.1 Atribuição
```
Id = Expr .
```
A expressão à direita deve ser **compatível em tipo** com a variável.

### 4.2 Leitura
```
monee ( Id ) .
```
Lê uma linha do teclado e converte automaticamente de acordo com o tipo declarado de `Id`.

### 4.3 Escrita
```
hei ( Expr ) .
```
Imprime o valor da expressão. Para texto literal, basta uma string entre aspas duplas.

### 4.4 Condicional
```
ramo ( Cond ) {
  Cmd+
} yro {
  Cmd+
}
```
A cláusula `yro { ... }` (else) é opcional. 

### 4.5 Repetição `aja` (while)
```
aja ( Cond ) {
  Cmd+
}
```

### 4.6 Repetição `japo … aja` (do…while)
```
japo {
  Cmd+
} aja ( Cond ) .
```

### 4.7 Repetição `rupi` (for)
```
rupi ( Id = Expr . Cond . Id = Expr ) {
  Cmd+
}
```
Forma `(init . cond . passo)`. Note que `init` e `cond` terminam com `.`, mas o `passo` não — ele já está dentro dos parênteses.

**Geração de código.** Quando o laço é um contador inteiro canônico — a mesma
variável em `init`, `cond` e `passo`, com `passo` na forma `i = i + k`
(ou `i = i - k`) e limite inteiro — o transpilador emite o idiomático
`for i in range(start, stop, step)`:

- `i < b` → `range(a, b)`;  `i <= b` → `range(a, b+1)` (literais são dobrados:
  `i <= 3` → `range(a, 4)`; expressões viram `range(a, b + 1)`).
- `i > b` / `i >= b` → passo negativo, ex.: `range(a, b, -1)` / `range(a, b-1, -1)`.
- passo `+1` crescente omite o terceiro argumento de `range`.

Laços fora desse formato (passo como `i = i * 2`, limite `float`, variáveis que
não coincidem, etc.) caem na tradução genérica `init; while cond: … ; passo`.

---

## 5. Expressões e precedência

A gramática é estratificada — `expr → term → fator` — para garantir precedência aritmética sem recursão à esquerda.

```
expr   ::= term ( ("+" | "-") term )*
term   ::= fator ( ("*" | "/") fator )*
fator  ::= NUMERO_INT
         | NUMERO_DEC
         | STRING
         | "anete"
         | "japu"
         | IDENT
         | "(" expr ")"
```

Operadores `*` e `/` têm precedência maior que `+` e `-`. Parênteses são sempre respeitados.

### Condições
```
cond   ::= expr op_rel expr
op_rel ::= "<" | ">" | "<=" | ">=" | "==" | "!="
```

---

## 6. Sistema de tipos

### 6.1 Tipos
- `papy` — inteiro com sinal (mapeado para `int`)
- `papyvore` — ponto flutuante (mapeado para `float`)
- `nee` — cadeia de caracteres (mapeado para `str`)
- `anetepa` — booleano (mapeado para `bool`)

### 6.2 Regras de operação

| Operador | Tipos aceitos | Tipo do resultado |
|------------|------------|------------|
| `+` `-` `*` `/` | `papy`/`papyvore` (mistura promove a `papyvore`) | número |
| `+` | `nee` + `nee` (concatenação) | `nee` |
| `<` `>` `<=` `>=` | numéricos compatíveis | `anetepa` |
| `==` `!=` | mesmo tipo | `anetepa` |

Regras de promoção:
- Atribuir `papy` em variável `papyvore` é **permitido** implicitamente.
- Atribuir `papyvore` em variável `papy` é **proibido**.
- Strings e booleanos não participam de operações aritméticas.
- A divisão `/` resulta em `papyvore` se houver algum `papyvore`, senão gera `papy` (divisão inteira).

---

## 7. Equivalência com Python (visão geral)

| Construção Tupi | Python gerado |
|---|---|
| `tekoha … opa.` | Envolto em `def main(): … ; main()` |
| `papy x.` | `x: int = 0` |
| `papyvore x.` | `x: float = 0.0` |
| `nee x.` | `x: str = ""` |
| `anetepa x.` | `x: bool = False` |
| `x = <expr>.` | `x = <expr>` |
| `hei(<expr>).` | `print(<expr>)` |
| `monee(x).` (x int) | `x = int(input())` |
| `monee(x).` (x float) | `x = float(input())` |
| `monee(x).` (x str) | `x = input()` |
| `monee(x).` (x bool) | `x = input().strip().lower() in ("true","anete","1")` |
| `ramo (c) { … } yro { … }` | `if c: …` / `else: …` |
| `aja (c) { … }` | `while c: …` |
| `japo { … } aja (c).` | `while True: …; if not c: break` |
| `rupi (i = a . i < b . i = i + p) { … }` | `for i in range(a, b, p): …` (contador canônico; senão `while`) |
| `anete` / `japu` | `True` / `False` |

---

## 8. Gramática completa (forma BNF)

Equivalente à definida em `tupi.lark`:

```
Prog        → "tekoha" Decls Bloco "opa" "."
Decls       → Decl*
Decl        → Tipo IDENT ("," IDENT)* "."
Tipo        → "papy" | "papyvore" | "nee" | "anetepa"
Bloco       → Cmd+
Cmd         → CmdLeitura | CmdEscrita | CmdAtrib | CmdIf
            | CmdWhile  | CmdDoWhile | CmdFor
CmdLeitura  → "monee" "(" IDENT ")" "."
CmdEscrita  → "hei" "(" Expr ")" "."
CmdAtrib    → IDENT "=" Expr "."
CmdIf       → "ramo" "(" Cond ")" "{" Cmd+ "}" ("yro" "{" Cmd+ "}")?
CmdWhile    → "aja"   "(" Cond ")" "{" Cmd+ "}"
CmdDoWhile  → "japo"  "{" Cmd+ "}" "aja" "(" Cond ")" "."
CmdFor      → "rupi"  "(" ForInit Cond "." ForStep ")" "{" Cmd+ "}"
ForInit     → IDENT "=" Expr "."
ForStep     → IDENT "=" Expr
Cond        → Expr OpRel Expr
OpRel       → "<" | ">" | "<=" | ">=" | "!=" | "=="
Expr        → Term  ( ("+"|"-") Term  )*
Term        → Fator ( ("*"|"/") Fator )*
Fator       → NUMERO_INT | NUMERO_DEC | STRING
            | "anete" | "japu" | IDENT | "(" Expr ")"
NUMERO_INT  → [0-9]+
NUMERO_DEC  → [0-9]+ "." [0-9]+
IDENT       → [A-Za-z_][A-Za-z0-9_]*
STRING      → '"' .*? '"'
```

---

## 9. Exemplo de compilação lado a lado

`programa.tg`:
```
tekoha
  papy a, b, c.
  papyvore d.

  hei("Programa Teste").
  hei("Digite A").
  monee(a).
  hei("Digite B").
  monee(b).

  ramo (a < b) {
    c = a + b.
  } yro {
    c = a - b.
  }

  hei("C =").
  hei(c).

  d = c / (a + b).
  hei("D =").
  hei(d).
opa.
```

`programa.py` (saída gerada):
```python
def main():
    a: int = 0
    b: int = 0
    c: int = 0
    d: float = 0.0

    print("Programa Teste")
    print("Digite A")
    a = int(input())
    print("Digite B")
    b = int(input())

    if a < b:
        c = a + b
    else:
        c = a - b

    print("C =")
    print(c)

    d = c / (a + b)
    print("D =")
    print(d)

if __name__ == '__main__':
    main()
```

---

## 10. Visualização da Árvore Sintática (Parse Tree)

O transpilador também permite visualizar a árvore sintática gerada pelo parser (antes da AST simplificada), mostrando exatamente como a gramática processa o arquivo. Esse formato é útil para entender o funcionamento interno e para visualização clássica de compiladores.

Para ver a árvore de um código, utilize o comando `tree` no CLI:

```bash
python -m tupi.cli tree examples/01_ola_mundo.tg
```

Saída gerada:
```
start
  program
    decls
    bloco
      cmd_escrita
        expr
          term
            fator_str  "Mba_eichapa ko yvy!"
```

