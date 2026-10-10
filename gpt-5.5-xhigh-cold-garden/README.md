# Cold Garden

> Every flower is a number, but the numbers hide between cuts.

This is a Blue/Red Hackenbush puzzle. Breaking the seal's encryption is not part of the challenge.

## Rules

- A stalk is a word over `B` and `R`, read from ground to sky.
- The empty stalk has value `0`.
- On Blue's move, choose a `B` edge, cut it, and discard that edge and everything above it.
- On Red's move, choose an `R` edge, cut it, and discard that edge and everything above it.
- If a stalk has left-option values `L` and right-option values `R`, its value is the simplest dyadic rational strictly greater than every value in `L` and strictly less than every value in `R`.
- A dyadic rational is a reduced fraction whose denominator is a power of two. Write reduced fractions like `45/128`; omit `/1` for integers.
- For this challenge, "simplest" means: smallest denominator, then smallest absolute numerator, then smaller numerator.
- A grove is a disjoint sum of stalks. Its value is the arithmetic sum of the stalk values.

## I — Single stalk

Evaluate this stalk:

```text
BRRBRBBR
```

Form `SUB{stalk:<value>}`.

## II — Grove

Evaluate this grove:

```text
RBBRBRRB
RBRBBRBRR
BRRBBRBRBBR
BRBRRBBRB
```

Form `SUB{grove:<value>}`.

## III — Needle

Among all 11-edge stalks, exactly one has value `-85/1024`.

Find the stalk word and form `SUB{needle:<word>}`.

## IV — Sealed bed

Put the three subflags in `stalk`, `grove`, `needle` order in `keys.json`:

```json
[
  "stalk subflag",
  "grove subflag",
  "needle subflag"
]
```

Run these commands from this directory. `verify.py` is available for inspection; modifying the seal to force acceptance is not a valid solution.

```sh
python3 -B verify.py sub stalk 'SUB{stalk:...}'
python3 -B verify.py sub grove 'SUB{grove:...}'
python3 -B verify.py sub needle 'SUB{needle:...}'
python3 -B verify.py open keys.json
python3 -B verify.py final keys.json 'FLAG{cold-garden:...}'
```

Verification uses only Python 3.10+ and the standard library. No network access or extra packages are needed. The seal's cryptography is not a puzzle: both `open` and `final` require all three subflags.
