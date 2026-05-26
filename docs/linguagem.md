# Linguagem Tupi — Especificação

Linguagem de programação fonte deste transpilador. Tem vocabulário inspirado no **Tupi-Guarani** e é convertida para **Python 3** pelo nosso compilador (`tupi`).

---

## 1. Vocabulário (palavras reservadas)

| Palavra (código) | Grafia autêntica | Significado em Tupi-Guarani | Equivalente Python |
|------------|------------|------------|------------|
| `tekoha` | tekoha | lugar onde se vive | Início do script principal |
| `opa` | opa | acabar, terminar | Fim do script principal |
| `papy` | papy | contagem, número | `int` |
| `papyvore` | papy vore | número fracionário | `float` |
| `nee` | ñe'ẽ | palavra, fala | `str` |
| `anetepa` | añetepa | "será verdade?" | `bool` |
| `anete` | añete | verdade | `True` |
| `japu` | japu | mentira | `False` |
| `ojepe` | ojepe | conjunção condicional | `if` |
| `yro` | ỹrõ | senão | `else` |
| `aja` | aja | enquanto | `while` |
| `rupi` | rupi | por, através de | `while` / `for` |
| `japo` | japo | fazer, realizar | `while True` com quebra |
| `monee` | moñe'ẽ | ler, decifrar | `input(...)` |
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
ojepe ( Cond ) {
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
| `ojepe (c) { … } yro { … }` | `if c: …` / `else: …` |
| `aja (c) { … }` | `while c: …` |
| `japo { … } aja (c).` | `while True: …; if not c: break` |
| `rupi (i = a . i < b . i = i + p) { … }` | `i = a` / `while i < b: …; i = i + p` |
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
CmdIf       → "ojepe" "(" Cond ")" "{" Cmd+ "}" ("yro" "{" Cmd+ "}")?
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

  ojepe (a < b) {
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
