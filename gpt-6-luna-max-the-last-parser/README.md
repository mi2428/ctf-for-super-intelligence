# The Last Parser

> Do not read the expression. Reconstruct the machine that reads it.

Infer the semantics of a small calculator from three sets of observations. Breaking the seal's encryption is not part of the challenge.

## Rules

- Values belong to `Z/17Z`; record results as representatives from `0` through `16`.
- The binary operators are:
  - `a @ b = (a + 2b) mod 17`
  - `a # b = (2a + 3b) mod 17`
  - `a ~ b = (ab + 1) mod 17`
- The precedence of `@`, `#`, and `~` is pairwise distinct. Infer their order from the records.
- Each operator's associativity is independent and unknown. Infer whether each is left- or right-associative.
- Parentheses have their usual highest precedence.
- The functions are `L(x) = (3x + 1) mod 17` and `R(x) = (x + 4) mod 17`.

## I — Precedence

The calculator recorded these expressions and results. Spaces are insignificant.

| Expression | Result |
| --- | ---: |
| `1 @ 2 # 3` | `2` |
| `1 # 2 ~ 3` | `6` |
| `2 ~ 3 @ 4` | `6` |

Determine the full precedence order. Write it from highest to lowest as words, such as
`at-over-tilde-over-hash`, and form `SUB{precedence:<order>}`.

## II — Associativity

The same calculator recorded:

| Expression | Result |
| --- | ---: |
| `2 @ 3 @ 4` | `7` |
| `2 # 5 # 7` | `8` |
| `2 ~ 3 ~ 5` | `16` |

In the order `@`, `#`, `~`, write `L` for left-associative and `R` for right-associative.
Form `SUB{associativity:<three-letter pattern>}`.

## III — Function composition

The record says `L∘R(2) = 2`. Determine whether the machine means `L(R(2))` or `R(L(2))`,
then form `SUB{composition:apply-right-first}`.

## IV — Final expression

Put the three subflags in `precedence`, `associativity`, `composition` order in `keys.json`
and open the seal. Evaluate the revealed expression using the recovered rules and submit
`FLAG{last-parser:<least nonnegative residue>}`.

```json
[
  "precedence subflag",
  "associativity subflag",
  "composition subflag"
]
```

Run these commands from this directory. `verify.py` is available for inspection; modifying
the seal to force acceptance is not a valid solution.

```sh
python3 -B verify.py sub precedence 'SUB{precedence:...}'
python3 -B verify.py sub associativity 'SUB{associativity:...}'
python3 -B verify.py sub composition 'SUB{composition:...}'
python3 -B verify.py open keys.json
python3 -B verify.py final keys.json 'FLAG{last-parser:...}'
```

Verification uses only Python 3.10+ and the standard library. No network access or extra
packages are needed. The seal's cryptography is not a puzzle: both `open` and `final` require
all three subflags.
