# The False Ledger — Organizer Solution

Do not distribute this file or the adjacent reference solver with the challenge directory.

## Flags

```text
SUB{repair:22:3ebe58631f2d6c8fb0df27bce8e3db00f25dcfc74c8c18cc2b178d30d52611c9}
SUB{lineage:12:d75249ce3ad664c89283c295f81acd6b28aa72f7beef69479dfd599aca73c46f}
SUB{reassure:21:617efea553f9ad8e5f97e23c809113cdef87a78ea769dcf0fe23a9a878887c61}
FLAG{false-ledger:12:19:1f9c:0b7ef735377db795493c6ec19e75327552b048321e6f11352de18f9fa17abf63}
```

## Representation

Treat every row `(person, seat)` as an edge of a bipartite graph. A valid row set is a matching.
For a valid mask `R`, precompute `ext(R)`, the mask of rows that can be added while preserving validity.
Then

```text
R is a repair of U  iff  R is contained in U and ext(R) intersects U trivially.
```

There are only 148 valid masks, so this criterion checks every universe without repeatedly searching all `2^14` row sets.

## I — Repair

Enumerating every valid mask and retaining the inclusion-maximal masks in `T` gives 22 repairs.
Eight contain three rows and fourteen contain four rows; keeping only maximum-cardinality matchings would lose the former.

```text
00a1
010c
0264
02a2
0302
0314
0461
050a
0511
0841
084c
088a
0891
1088
1240
1290
1448
2024
2422
2802
2814
3410
```

Applying rule M produces the `repair` sub-flag above.

## II — Lineage

`Q0` is monotone. Every minimal witness therefore has one A row, one B row, and one C row; deleting any of the three destroys the witness.
Enumerate their Cartesian product and retain exactly the triples with equal A/C zones and the opposite B zone.

```text
0061
0062
008c
0094
010c
0114
1088
1090
1108
1110
2021
2022
```

Six of these masks are invalid matchings. They still belong to the raw lineage because this stage does not repair the table.
Applying M produces the `lineage` sub-flag.

## III — Reassure

For every deletion mask `D`, form `U = T \ D`, enumerate `repair(U)` with the extension criterion, and test `Q0` on every repair.
Exactly these 21 masks satisfy the universal condition:

```text
1b9c
1bdd
1f9c
1fdd
2c63
2c6b
2d67
2d6f
2e63
2e6b
2e73
2f67
2f6f
2f77
3b9e
3ce3
3ceb
3ee3
3eeb
3ef3
3f9e
```

The only inclusion-minimal masks among them are `1b9c` and `2c63`, but the requested answer contains all 21.
The property is not upward closed: `1b9c` is good, while additionally deleting `t00` gives `1b9d`, which is not good because deletion changes the set of maximal repairs.

## IV — Final audit

The three sub-flags authenticate and decrypt this task:

```json
{
  "query": {
    "name": "Q1",
    "persons": ["B", "D"],
    "zone_relation": "equal"
  },
  "weights": [2, 3, 1, 4, 2, 2, 3, 2, 1, 3, 2, 2, 2, 3]
}
```

Thus `Q1(R)` asks whether a B row and a D row in `R` use seats in the same zone.
Recompute all repairs after each deletion and require every repair to satisfy `Q0` and falsify `Q1`.
The feasible deletion masks and their costs are:

```text
1f9c  19
1fdd  24
2e63  20
2e6b  24
2e73  22
2f67  22
2f6f  26
2f77  24
3ee3  24
3eeb  28
3ef3  26
3f9e  25
```

Their M digest is `0b7ef735377db795493c6ec19e75327552b048321e6f11352de18f9fa17abf63`.
The unique minimum-cost mask is `1f9c`, with cost 19, yielding the final flag above.

## Reproduction

From the repository root, run:

```sh
python3 -B answers/gpt-5.6-sol-max-false-ledger.py
```

The standard-library solver independently rebuilds every answer set, authenticates and decrypts the seal, checks all four verifier commitments, and rejects a bad flag and a modified seal.
