# Blind Atrium — organizer's solution

**Spoilers. Do not distribute this directory to challengers.**

## Flags

```text
SUB{ward:29e0039d8cc28b5b9455fbd3830de5db8ac1817035b90ce817750b1df2c40b8b}
SUB{once:1c4a48b721d812c7bb6a191f3acb9e5d3342a466b0a5114bbf83bdd76d19cab2}
SUB{omega:28a0a8d489ca17249fb3ec534cb86704aa1c579ef4c9d593c26c1161cc6e75e5}
FLAG{blind-atrium:2:a0b1b1c0c0a1}
```

Run the executable reference solution and regression checks from the repository root:

```sh
python3 -B answers/gpt-6-astra-max-blind-atrium.py
```

It derives the sub-flags from the arena, opens the seal, finds the optimal controller, checks its flag, and tests the CLI using an isolated copy of the challenge directory. It uses only the standard library. Temporary key files are removed automatically. Do not use Python's `-O` option: the regression checks use assertions.

## 1. Track the right information

There are three observation classes of five states each, so there are `3(2^5 - 1) = 93` allowed initial sets.
Represent state sets by bit masks, with state `q` occupying bit `q`.
For an observation `z`, write `Q_z = {q : obs[q] = z}` and define:

```text
Post(B,a)   = union of T(q,a) over q in B
Post(B,a,z) = Post(B,a) intersect Q_z
```

Discard empty observation branches. A controller cannot choose the hidden successor, so its controllable predecessor operator is:

```text
CPre(X) = {s : some action has ALL its possible observation successors in X}
```

The order of the quantifiers is essential: one common action must work for every currently possible hidden state.

### Ward

The current belief `B` suffices for safety. It is safe exactly when `B` is disjoint from `bad`.
Start with all safe beliefs and repeatedly remove any belief with no action whose successors all remain in the set.
The limit is the greatest fixed point `νX.(Safe ∩ CPre(X))`.

### Once

A current belief does not record which paths have already visited the target.
Use a pair `(B,O)`, where `O ⊆ B` consists of endpoints of paths that have **not yet visited** the target.
The initial pair is `(B, B \ target)`. After action `a` and observation `z`:

```text
B' = Post(B,a,z)
O' = Post(O,a,z) \ target
```

In particular, empty `O` stays empty. Solve ordinary sure reachability to `O = ∅`, using the least fixed point:

```text
μY.({(B,O) : O = ∅} ∪ CPre(Y))
```

This does not require simultaneous physical occupancy of the target. It only requires that every compatible path has visited it at some point.
For a fixed winning strategy, the tree of target-avoiding finite plays is finitely branching. If its depth were unbounded, König's lemma would give an infinite target-avoiding play. Thus sure eventual visiting admits a finite bound on the first visit, and the reduction loses no winning strategies.

### Omega

Use the same pair, but interpret `O` as the endpoints of paths still owing a visit **during the current round**.
When `O` is nonempty, update it as above. When `O` is empty, start the next round on the next transition:

```text
B' = Post(B,a,z)
O' = B' \ target                 if O is empty
O' = Post(O,a,z) \ target        otherwise
```

The new objective is to reach `F = {(B,O) : O = ∅}` infinitely often.
Every completed round certifies a visit on every compatible path.
Conversely, a round that never completes supplies an infinite target-avoiding suffix by the same finite-branching argument.
Hence this breakpoint construction preserves sure infinite recurrence.

Solve the resulting fully observed game with the nested fixed point:

```text
νZ.μY.((F ∩ CPre(Z)) ∪ CPre(Y))
```

The reference implementation restricts the inner iteration to `Z`; starting the outer iteration from all states makes this equivalent.
There are only 93 reachable lifted states for Ward, 143 for Once, and 132 for Omega, when exploration starts from all 93 legal initial sets.

## 2. Recover the complete winning families

The winning families are downward closed under nonempty subsets: a strategy that handles a larger initial set also handles any smaller one.
The following inclusion-maximal masks therefore specify the **complete** answers compactly:

| Part | Winning initial sets | Inclusion-maximal masks |
| --- | ---: | --- |
| Ward | 55 | `000b`, `000c`, `08b0`, `2740` |
| Once | 77 | `100f`, `08b0`, `2740` |
| Omega | 65 | `100b`, `100c`, `08b0`, `2740` |

Take every nonzero submask of these maxima, deduplicate, sort, format as four lowercase hex digits plus LF, and hash. Hashing only the maxima is incorrect.
The reference program independently checks that this expansion equals its fixed-point results for all 93 candidates.

Two small features explain important traps:

- **Unknown phase:** From `B = {0,1}`, repeating `b` swaps rooms 0 and 1 forever. Every actual play visits room 0 infinitely often, but the belief stays `{0,1}` and is never contained in `target`. A belief-only reachability or recurrence test misses this winning set.
- **Already visited is not still visiting:** From `{1,2}`, action `b` sends room 1 to target room 0, while room 2 has already satisfied Once at time zero and may fall into room 14. Once is winnable, but Omega is not: choosing `a` or `c` loses forever from room 1, while choosing `b` loses forever from room 2.

Requiring beliefs to be wholly contained in `target` gives only 62 Once winners and 61 Omega winners, instead of 77 and 65. Thus the distinction is not merely theoretical on this instance.

## 3. Open the final task

The verifier checks each complete sub-flag before deriving the key. It then authenticates and decrypts the sealed JSON.
Both the final objective and its flag commitment are inside the seal; the public verifier does not contain a standalone commitment to the small final-controller search space.

The final initial set is `{4,11}`. Every play must avoid `{12,14}` and visit both `{0,2,6,10}` and `{11}` infinitely often.
The memory starts at 0. A table cell uses the current memory and current observation to choose both an action and the memory for the next step.

## 4. Minimize the finite controller

For a fixed table, construct the directed product graph on `(room, memory)` from the initial pairs `(4,0)` and `(11,0)`.
Reject the table if any reachable room is forbidden.
For each target set separately, delete all target vertices from the **entire reachable product graph** and test whether any directed cycle remains.

- A remaining cycle can be reached after a finite prefix and then followed forever, defeating recurrence.
- Conversely, an infinite target-avoiding suffix in a finite graph must contain a cycle.

This is a necessary and sufficient test. Merely requiring each reachable strongly connected component to intersect the target is unsound: an SCC may also contain a smaller target-avoiding cycle.

A one-memory-state controller has `3^3 = 27` possible tables. None wins.
A two-memory-state table has six cells with six choices per cell, for `6^6 = 46,656` tables.
Enumerate them in ASCII order using the cell order specified in the task. The first winning table is number **4,706** (one-based):

| Current memory | Observation 0 | Observation 1 | Observation 2 |
| --- | --- | --- | --- |
| 0 | `a0` | `b1` | `b1` |
| 1 | `c0` | `c0` | `a1` |

Its complete encoding is `a0b1b1c0c0a1`. The `a0` cell is unreachable but must still be encoded and minimized.
The reachable graph is particularly simple:

```text
Prefix: (11,0) -> (9,1) -> (3,1) -> (8,0)
Cycle:   (8,0) -> (11,1) -> (4,0) -> (2,1) -> (8,0) -> ...
```

The first line is the prefix from initial room 11; initial room 4 starts directly on the four-vertex cycle in the second line.
No forbidden room is visited. Each cycle visits room 2 and room 11.
Exhausting all 27 one-state tables proves the memory lower bound, and rejecting the 4,705 earlier two-state encodings proves lexical minimality. The witness supplies the matching upper bound.

## Regression coverage

The reference program checks the exact winning families, the two misleading belief-only reductions, unknown phase, a one-shot target, a constant-belief game requiring alternating actions, incompatible safe actions, and a target-containing SCC with a losing self-loop.
It also checks all sub-flags, final decryption and submission, missing/reordered/duplicated/wrong-type keys, malformed JSON, missing files, non-ASCII flags, modified seals, and command exit statuses.

Only the challenge directory should be distributed. This solution, the reference program, and any design artifacts are organizer material.
