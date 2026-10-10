# The False Ledger

> A database can lie without any row being false.

Fourteen booking rows survived a failed merge. Every row may be genuine, but the table violates two keys.
Recover its repairs, its raw evidence, and the deletions that make an answer certain. Only then may you open the final audit.

## Distribution and rules

- This directory is self-contained. `ledger.json` is the public table, `final.seal.json` contains the sealed final task, and `verify.py` checks flags.
- Python 3.10 or newer and the standard library are sufficient. No network access, external facts, or expensive cryptanalysis is needed.
- You may inspect `verify.py` and write any programs you like. Modifying the distribution, brute-forcing verifier commitments, or reading undistributed answers or Git history is not a solution.
- Collect all three sub-flags before opening the final task. Submit every sub-flag, the final flag, and your derivation.

## The ledger

The array `rows` is ordered. Row `t00` has index 0, row `t01` has index 1, and so on through index 13.
Row IDs are fixed identities: never rename rows, people, or seats, and never quotient by a permutation.

For a set of row indices `S`, define its mask

```text
m(S) = sum(2^i for i in S).
```

Write every mask as exactly four lowercase hexadecimal digits, including leading zeroes.
The full table is `T = {0,...,13}`, whose mask is `3fff`.

A set of rows is **valid** when no two distinct selected rows have the same `person` and no two have the same `seat`.
For any `U` contained in `T`, a **repair of U** is an inclusion-maximal valid subset of `U`:

- it is valid; and
- adding any one row from `U` that it does not already contain makes it invalid.

Maximal means maximal by inclusion, not largest cardinality. Repairs are rebuilt from the stated `U`; they are not inherited from repairs of `T`.
The only repair of the empty table is the empty set.

The public Boolean query `Q0(S)` is true exactly when there are rows `a,b,c` in `S` with persons `A,B,C`, respectively, such that

```text
zone(seat(a)) = zone(seat(c)) != zone(seat(b)).
```

The zones are given in `ledger.json`. Unless a stage explicitly says otherwise, `S` need not be valid.

## Common recording rule M

Given a finite set of masks, remove duplicates, sort by integer value, and write each as four lowercase hexadecimal digits followed by one LF.
The last line also has an LF. The empty set is encoded as zero bytes.

Let `N` be the number of masks in decimal without leading zeroes, and let `H` be the lowercase SHA-256 digest of the exact bytes above.
The three sub-flags use the form `SUB{name:N:H}`.

## I — Repair: what could the clerk have meant?

Find every repair of the full table `T`.
Apply M to their masks and submit

```text
SUB{repair:N:H}
```

Do not discard a repair merely because another repair has more rows.

## II — Lineage: what is the smallest raw evidence?

Find every inclusion-minimal set `S` contained in the raw table `T` for which `Q0(S)` is true.
Minimality is by inclusion: `Q0(S)` is true, but `Q0(S')` is false for every proper subset `S'` of `S`.

This stage is about the raw table, not its repairs. Do not impose validity on `S` and do not discard mutually conflicting witnesses.
Apply M and submit

```text
SUB{lineage:N:H}
```

## III — Reassure: which erasures make the answer certain?

For a deletion set `D` contained in `T`, define

```text
Good(D)  iff  Q0(R) is true for every R in repair(T \ D).
```

Find **every** `D` for which `Good(D)` holds, not only the inclusion-minimal or least-cardinality ones.
The repairs must be recomputed after deleting `D`.
Apply M to all such deletion masks and submit

```text
SUB{reassure:N:H}
```

## IV — The sealed audit

Put the three exact sub-flags into `keys.json` in `repair`, `lineage`, `reassure` order.

```json
[
  "repair sub-flag",
  "lineage sub-flag",
  "reassure sub-flag"
]
```

Opening the seal reveals a two-person query `Q1` and one positive deletion weight for every row.
For the revealed `persons = [P,Q]` and `zone_relation = "equal"`, `Q1(S)` is true exactly when `S` contains a row for `P` and a row for `Q` whose seats have the same zone.

A deletion set `D` is **feasible** when every repair `R` of `T \ D` satisfies both conditions:

```text
Q0(R) is true, and Q1(R) is false.
```

Find every feasible deletion set. Apply M to their masks to obtain `N` and `H`.
For each feasible `D`, its cost is the sum of `weights[i]` over all deleted row indices `i`.
Choose the feasible `D` minimizing `(cost, m(D))` lexicographically, where the second component is the mask as an integer.
Let `C` be its decimal cost without leading zeroes and `M` its four-digit lowercase hexadecimal mask.

Submit

```text
FLAG{false-ledger:N:C:M:H}
```

Run these commands with this directory as the working directory:

```sh
python3 -B verify.py sub repair 'SUB{repair:N:H}'
python3 -B verify.py sub lineage 'SUB{lineage:N:H}'
python3 -B verify.py sub reassure 'SUB{reassure:N:H}'
python3 -B verify.py open keys.json
python3 -B verify.py final keys.json 'FLAG{false-ledger:N:C:M:H}'
```

`open` and `final` validate all three keys. Missing, incorrect, or reordered keys are rejected.
Successful `sub` and `final` commands print `OK`; successful `open` prints the authenticated final task as JSON.
