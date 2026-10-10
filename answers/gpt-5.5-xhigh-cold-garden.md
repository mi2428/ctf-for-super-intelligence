# Cold Garden — Author's Solution

**Do not distribute this file to challengers.**

## All flags

```text
SUB{stalk:45/128}
SUB{grove:85/1024}
SUB{needle:RBBBBRBRBRB}
FLAG{cold-garden:535/512}
```

## Recurrence

For a stalk `s`, each legal cut at index `i` leaves the prefix `s[:i]`.

```text
V("") = 0
V(s) = simplest({V(s[:i]) for s[i] == B} | {V(s[:i]) for s[i] == R})
```

The `simplest` value is the reduced dyadic rational in the open interval with the smallest denominator, then the smallest absolute numerator, then the smaller numerator.

## I — Single stalk

Applying the recurrence to `BRRBRBBR` gives:

```text
V(BRRBRBBR) = 45/128
```

So the subflag is `SUB{stalk:45/128}`.

## II — Grove

The four stalk values are:

| Stalk | Value |
| --- | ---: |
| `RBBRBRRB` | `-45/128` |
| `RBRBBRBRR` | `-151/256` |
| `BRRBBRBRBBR` | `429/1024` |
| `BRBRRBBRB` | `155/256` |

Their sum is:

```text
-360/1024 - 604/1024 + 429/1024 + 620/1024 = 85/1024
```

So the subflag is `SUB{grove:85/1024}`.

## III — Needle

Enumerating the `2^11` possible 11-edge stalks with the same recurrence shows that exactly one has value `-85/1024`:

```text
RBBBBRBRBRB
```

So the subflag is `SUB{needle:RBBBBRBRBRB}`.

## IV — Sealed bed

With the three subflags in order, the seal opens to this final grove:

```text
BBRBRBRRBBR
BRRBBRBRBBR
RBBRBRRB
RBRBBRBRR
RBBBBRBRBRB
```

The final stalk values are:

| Stalk | Value |
| --- | ---: |
| `BBRBRBRRBBR` | `845/512` |
| `BRRBBRBRBBR` | `429/1024` |
| `RBBRBRRB` | `-45/128` |
| `RBRBBRBRR` | `-151/256` |
| `RBBBBRBRBRB` | `-85/1024` |

Their sum is:

```text
1690/1024 + 429/1024 - 360/1024 - 604/1024 - 85/1024 = 535/512
```

So the final flag is `FLAG{cold-garden:535/512}`.

## Verification

```sh
cd gpt-5.5-xhigh-cold-garden
python3 -B verify.py sub stalk 'SUB{stalk:45/128}'
python3 -B verify.py sub grove 'SUB{grove:85/1024}'
python3 -B verify.py sub needle 'SUB{needle:RBBBBRBRBRB}'
printf '["SUB{stalk:45/128}","SUB{grove:85/1024}","SUB{needle:RBBBBRBRBRB}"]\n' > keys.json
python3 -B verify.py open keys.json
python3 -B verify.py final keys.json 'FLAG{cold-garden:535/512}'
rm keys.json
```
