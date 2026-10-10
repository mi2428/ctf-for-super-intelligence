# Folded Tribunal — Organizer's Solution

**Do not distribute this document or the adjacent reference program.**
The complete challenger distribution is `gpt-6.1-sol-max-folded-tribunal/` only.

## All sub-flags and one valid final representative

```text
SUB{core:62:594b3fe73cdb5fcc947e47895c919f6c9267669372ed63c782bf04475273d5d0}
SUB{veil:190:6598f0103e15580aebed0b7b34d724d7b8360983f26eac1bf4ff4641d6b6e4ec}
SUB{transport:18:f5623f2706a8047448a6841e3bb764f8125e549deb7eedca91cbedb5d18f0da8}
FLAG{folded-tribunal:14:ce38f2915f421da2020f10604fcf571bf795360f11cfdcafe20e831e7372cd81}
```

Run the complete constructive solution and its regression checks from the
repository root:

```sh
python3 -B answers/gpt-6.1-sol-max-folded-tribunal.py
```

It constructs the infinite languages exactly, computes their canonical minimal
automata, opens the actual seal, constructs a 14-memory controller, checks the
lower-bound structure, and verifies an isolated full submission through the
actual CLI. No dependencies, network, persistent generated files, or finite
language-sampling cutoff are needed. The temporary CLI fixtures are removed.
Multiple minimum controllers can yield different valid final flags; the one
above is returned for the canonical controller shown below.

## 1. Subgroup folding with a marking

Start with a based bouquet of the three supplied generator loops. Subdivide
each loop into edges labeled by the individual ambient letters, and add inverse
edges. Repeatedly fold equally labeled edges with the same source. The resulting
finite inverse graph recognizes subgroup membership: a reduced ambient word is
in the subgroup precisely when it labels a loop at the basepoint.

The folded graphs for `U,V,P,Q` have respectively **12, 16, 7, 11 vertices**, and
each has rank three, computed as `undirected edges - vertices + 1`. The supplied
three-generator tuples are therefore free bases. Indeed, their maps from a free
group of rank three onto the corresponding rank-three subgroup are isomorphisms
by Hopficity of finite-rank free groups.

Retain a marking over `x,X,y,Y,z,Z` to recover coordinates in the *supplied*
basis, not merely some spanning-tree basis. Before folding, mark the last edge
of generator loop `i` by `x`, `y`, or `z`; mark the other edges by the empty word.
Inverse edges have inverse markings. During a fold, suppose the two edges are

```text
u --l/m1--> v
u --l/m2--> w.
```

Merge `w` into `v`, retaining the basepoint if either is the basepoint. Put
`k=reduce(m1^-1 m2)`. Prefix every outgoing edge marking at `w` by `k`, and
suffix every incoming edge marking at `w` by `k^-1`. A loop at `w` receives both
changes. Duplicate folded edges must then have identical reduced markings.

After folding, choose a based spanning tree. If `p_v` is its path marking to
vertex `v`, replace the marking of `u --l/m--> v` by
`reduce(p_u m p_v^-1)`. Tree edges now have empty markings. Reading a **based**
loop gives its exact preimage in the supplied basis. Check every original
generator loop rewrites to its own single source letter, and every inverse
edge has the inverse marking.

The qualification "based" matters. For an internal loop at vertex `v`, the
ambient image is conjugated by the tree path to `v`; it need not equal the
unconjugated loop label.

## 2. Exact regular languages of group subsets

Construct ordinary finite automata for subgroup graphs, concatenated paths,
and directed labeled walks. A word label longer than one letter is subdivided
into a path; an empty label is an epsilon edge.

To pass from an automaton for words to the freely reduced representatives of
their group elements, use the following finite saturation:

1. Compute epsilon reachability, including zero-edge paths.
2. Whenever there is a path `p --l--> q --epsilon*--> r --l^-1--> s`, add an
   epsilon path from `p` to `s`.
3. Recompute epsilon reachability and repeat until no relation changes.
4. Determinize, intersect with the language of freely reduced strings, and
   minimize.

There are finitely many possible vertex pairs, so saturation terminates.
Every added epsilon path abbreviates a genuinely cancellable subword. Conversely,
an innermost inverse-pair deletion in any free reduction is eventually included;
induction on deletions proves completeness. Thus this is Benois *forward*
reduction of a rational language.

Do not mistake this for recognizing all unreduced representatives of a group
element. That inverse closure need not be regular: the words reducing to the
identity intersected with `a* A*` form `{a^n A^n : n>=0}`.

Normalize group subsets **before** intersection, difference, or complement.
For example, `{aA}` and `{epsilon}` represent the same group subset, despite
their disjoint unreduced string languages. Complement operations in the solver
are restricted to freely reduced strings.

## 3. Core and Veil

Intersect the two subgroup languages by a DFA product to obtain Core. Its
minimal complete all-string DFA has **62 states**, including its reachable
rejecting sink.

For `HK`, join the accepting basepoint of the `H` graph to the initial basepoint
of the `K` graph by an epsilon edge, accepting at the latter basepoint. Apply
forward reduction and normalization. Construct `KH` separately. Their
intersection, minus Core, gives the **190-state** Veil DFA.

This is not a free-product union in disguise. A useful underlying coordinate
system is

```text
r = abAB, p = bcBC, q = caCA.
H = <r^2, q, r p r^-1>
K = <r^3, p, r q r^-1>.
```

The published tuples are Nielsen changes of these bases. The root `r` satisfies

```text
r = r^-2 r^3 = r^3 r^-2.
```

It is therefore in both `HK` and `KH`, but in neither `H` nor `K`. Hence Veil
is not `(H union K) minus Core`. Meanwhile `r^6` is a nonidentity Core element
and is excluded from Veil. The two product orders also genuinely differ:
`abAcBC` is in `HK minus Core` but not in Veil.

## 4. Transport: two independent HNN families

The presentation is a multiple HNN extension of the free base group. Its four
legal pinch orientations are

```text
t h T -> phi(h)       if h is in H
T k t -> phi^-1(k)    if k is in K
s p S -> psi(p)       if p is in <P_0,P_1,P_2>
S q s -> psi^-1(q)    if q is in <Q_0,Q_1,Q_2>.
```

Here `psi(P_i)=Q_i`. Membership is determined by the relevant folded graph;
the marking supplies the source coordinates; substitute those coordinates in
the paired image tuple. Free reduction alone, literal substring matching of
the six relators, and arbitrary choices of a new subgroup basis are insufficient.

Parse a candidate as alternating freely reduced base words and individual
stable letters. Repeatedly collapse any legal adjacent inverse stable-letter
pair and merge its neighboring base words. Every collapse removes two stable
letters. If none remain, test whether the base word is empty. If stable letters
remain but no legal pinch exists, Britton's lemma certifies nonidentity. The
algorithm does not assume that the terminal reduced expression is unique.

The exact identity IDs are:

```text
01 02 03 05 08 13 15 16 18 20 21 24 25 26 27 29 32 34
```

All **36** supplied words have zero exponent sums in every generator, including
both stable letters, but only these **18** are identities. Cross-family pairs
are not pinches. For example, `tsTS` is nonidentity, as is `taTbtATB`, even though
both pass the exponent-sum test.

## 5. The hearing's infinite witness set

Open the seal with all three flags in their specified order. Delete edges with
nonidentity Transport IDs **before** constructing or reducing the walk automaton.
The surviving directed graph has three vertices and 18 edges; vertex `0` is
initial and vertex `2` is accepting. It has cycles and epsilon labels. Do not
silently add inverse edges.

Apply the same rational-language reduction to all accepting walks. The exact
reduced language `R` has a **54-state** minimal complete DFA. There is no walk
bound and no need to enumerate walks.

## 6. Pullbacks must preserve subgroup coordinates

For an injective map `e:F(x,y,z)->F(a,b,c)` and a reduced ambient regular
language `L`, compute `e^-1(L)` as follows:

1. Intersect the DFA for `L` with the based folded graph of `image(e)`.
2. Accept only at graph basepoint `0` and an accepting ambient DFA state.
3. Treat each product edge's *basis marking* as an output-word label.
4. Freely reduce this rational output language, intersect with reduced source
   strings, and minimize.

Each accepted ambient loop outputs its correct supplied-basis preimage.
Conversely, the reduced image of every desired source element has such an
accepted loop. Injectivity makes the output's reduced word equal to that source
element. This proves both directions without an inverse free-reduction closure.

Directly substituting generator images into an ambient DFA is wrong when
cancellation crosses image boundaries. Even the automorphism
`x->a, y->Ab, z->c` sends `xy` to the group element `b`, not to the unreduced
string `aAb`; the reference includes this regression.

Forward images are simpler: replace each source DFA transition by the
corresponding image-word path and apply forward reduction.

## 7. Eliminate the infinite universal quantifier

Define the rational group subsets

```text
A = { h in H : phi(h) is in R }
B = { k in K : phi^-1(k) is in R }.
```

Using the marked injections `U,V`, construct them exactly as

```text
A = U( V^-1(R) )
B = V( U^-1(R) ).
```

These are **268-state** and **433-state** reduced ambient languages,
respectively. Reversing either direction computes a different condition.

An *accusing* `HK` factorization exists exactly when `w` is in `AB`. An accusing
`KH` factorization exists exactly when `w` is in `BA`. Negating existence of
either kind of witness gives the complete final language

```text
Veil minus (AB union BA).
```

Thus the universal quantifier is eliminated by an exact set identity, not by
checking a finite set of candidate splits. Rational product, union, and
difference prove that the **intermediate verdict language** is regular and
construct its complete automaton. Its canonical minimal DFA has **1601 states**;
its recording digest is
`4bec3213acadf240d27970a33915801465620e4d5363f45005a9a0ecf10fab46`.

There is a concrete counterexample to changing "every" into "some". Put
`w=p=bcBC` and `j=r^6`. Both factorizations below are valid `HK` factorizations
of exactly the same element:

| Factorization | `phi(h) in R` | `phi^-1(k) in R` |
| --- | --- | --- |
| `h=1, k=p` | yes | yes |
| `h=j, k=j^-1 p` | no | no |

The second pair is safe, but the first pair accuses `p`. Consequently `p` must
be rejected. A chosen decomposition or an existential safe-pair test is wrong.
The reference verifies both actual pairs, their subgroup memberships, images,
and reduced products.

The verdict language is nonempty, infinite, and strictly smaller than Veil.
For example, `r=abAB` survives and `p=bcBC` does not. An executable pumping
certificate generated from a reachable coaccessible DFA cycle is

```text
u = baBAbaBAcaCbABabABa
v = bABabABabABabABabABabABa
z = cAC
```

Every `u v^n z`, for `n>=0`, is accepted. The cycle returns to the same state,
and its positive length distinguishes all these reduced strings. This is a
proof of infinitude, not extrapolation from sampled lengths.

## 8. Patrol: a relational probe and moving coordinates

The verdict automaton filters the patrol's guarded edges. After filtering,
models `e0,e1` have **43 and 44 physical states**. The queue is a permutation of
three jobs at three positions. In `e0`, inputs `X,Y` swap positions `(0,1)` and
`(1,2)`; `e1` interchanges the interpretations. Inputs are not commuting updates.

At a used hub, `a,b,c` serve the job at positions `0,1,2`; `p` is unsafe. Every
service is followed by an adversarial one- or two-letter input segment, then
marker `Z` and another hub. At input/marker states only acknowledgment `p` is
safe. The hidden service events must be `0,1,2,0,1,2,...`. Checking only physical
danger states, or only that each job appears in a reachable SCC, is wrong.

The initial one-shot probe emits two replies. In `e0` they are equal; in `e1`
they differ. The first reply alone reveals no model. The probe also applies
the two corresponding swaps to the queue: equal replies leave identity, while
`XY` and `YX` in `e1` give different three-cycles. Model identification without
tracking this effect does not suffice.

Let `queue[j]` denote the job at position `j`, and `next_job` the job owed by
the safety contract. Store the moving-frame permutation

```text
relative_queue[j] = (queue[j] - next_job) modulo 3.
```

There are six relative queues, not the naive `6*3` queue/clock combinations.
For each of the two learned models, use one memory per relative queue:

- At `H`, serve `relative_queue.index(0)` and subtract one modulo three from
  every queue value, accounting for the next owed job.
- At `X,Y`, acknowledge and swap the two appropriate positions.
- At `Z`, acknowledge and retain the relative queue.

This yields **12 known profiles**. Two more memories `U,V` suffice for the probe:

| Memory | H | X | Y | Z |
| --- | --- | --- | --- | --- |
| U, initially | `p,U` | `p,U` | `p,V` | `p,(e0,identity)` |
| V | `p,U`, unreachable | `p,(e1,probe(YX))` | `p,U` | `p,(e1,probe(XY))` |

Initial, first-`X`, and equal-completion roles alias at `U`. First-`Y` and
`XY`-completion alias at `V`. `YX`-completion can reuse a known profile, because
its next observation is `Z`. The table is therefore **14**, not a separate
probe-phase counter multiplied by all queue/clock states.

Here is the canonical numeric controller used for the displayed flag. Its
columns are `H,X,Y,Z`; action indices `0,1,2,3` mean `a,b,c,p`.

```json
{
  "initial": 0,
  "table": [
    [[3,0],[3,0],[3,1],[3,2]],
    [[3,0],[3,3],[3,0],[3,4]],
    [[0,5],[3,6],[3,7],[3,2]],
    [[2,8],[3,9],[3,10],[3,3]],
    [[1,3],[3,10],[3,11],[3,4]],
    [[1,12],[3,7],[3,13],[3,5]],
    [[1,7],[3,2],[3,12],[3,6]],
    [[0,13],[3,5],[3,2],[3,7]],
    [[0,4],[3,11],[3,9],[3,8]],
    [[1,11],[3,3],[3,8],[3,9]],
    [[2,9],[3,4],[3,3],[3,10]],
    [[0,10],[3,8],[3,4],[3,11]],
    [[2,2],[3,13],[3,6],[3,12]],
    [[2,6],[3,12],[3,5],[3,13]]
  ]
}
```

The invariant proves correct service order on every input choice. Every helper
segment is bounded, and every subsequent hub must serve. Hence all plays have
infinitely many services without a fairness assumption. The reachable products
have **114 and 115 nodes**, with **55 branching vertices each**. Every winning
controller must repeatedly traverse the branching segments; safe actions cannot
select a deterministic retreat. The branches modify queue positions, later
observations, and later required actions, not just an immediate duplicate path.

## 9. A tight lower bound for arbitrary controllers

The relevant memories are those **just before processing a fresh input segment**,
after the previous service. Do not identify a supplied controller's internal
labels with necessary memories without proof.

For a known model `e`, relative queue `q`, and legal segment word `W` of length
one or two, the next required hub response and following pre-input profile are

```text
required position = index of 0 in q sigma_e(W)
next profile      = (e, advance(q sigma_e(W))).
```

Here `sigma_e(W)` right-composes the position swaps; `advance` subtracts one
from each value. Safety forces these responses in *every* winning strategy.
No alternative safe action can avoid a profile. For each model the six-profile
transition graph is strongly connected, so all six are reached from any probe
outcome under suitable legal adversarial input segments.

All **66 pairs** of the 12 known profiles have a common legal observation
continuation requiring different future service-position actions. A finite
pair-product search constructs each separator; at most **two rounds** suffice.
This is a proof about the arena's forced-response functions, independent of
the exhibited controller. If two such histories shared a memory, determinism
would give the same future actions on their common suffix and violate safety
in one. Thus any winner needs at least **12** distinct memories at these points.

Now consider the two comparison histories after the probe's first `X` or first
`Y`, just before the last reply:

1. They cannot share a memory. A common last reply `X`, then `Z,H`, gives the
   `e0/identity` and `e1/probe(YX)` residuals. These are separable, immediately
   or on a subsequent common legal continuation.
2. Neither can share any of the 12 known pre-input memories. For a known model
   `e`, choose the last probe reply that identifies the **other fixed initial
   model**. That reply, `Z,H`, and a separating subsequent input continuation
   are legal in both histories but require different eventual actions.

This does not change a model midway through play. Both models allow the same
first probe reply, so that comparison memory is initially uniform; the proof
chooses a consistent fixed model for each complete counterplay. Future input
words are common legal observations in both models.

Therefore the comparison memories are two new classes beyond all 12 known
classes: **M>=12+2=14**. The construction above attains 14, proving the global
minimum without enumerating smaller tables. Phase-dependent state aliasing
cannot evade the argument, because the comparisons and known input points
are separated by actual common continuations, not by arbitrary phase labels.

At a learned model with physical queue identity, `XX` segments return to the
same physical-location belief after each service while the owed job advances.
The next forced actions differ. This is legitimate because the explicit
cyclic-order safety monitor is history-sensitive; it is not a false claim
that pure Buchi objectives distinguish identical-belief finite prefixes.

An independent position rotor fails: in `e0`, probe `XX`, serve position `a`
(job 0), then input `X`. The queue becomes `(1,0,2)`. A rotor's next position
`b` serves job 0 again instead of owed job 1. The correct joint moving frame
cannot be replaced by an independent position counter.

## 10. Canonicalization, gating, and adversarial regressions

For each requested DFA, minimize by right-language equivalence, discard
unreachable states, then BFS-number its quotient in alphabet order `aAbBcC`.
Serialize exactly as the public D rule specifies and hash the bytes. Do not
minimize relative to a reduced-input promise; nonreduced strings are rejected
by the actual all-string automaton and its reachable sink counts as a state.

The v2 sub-flag key uses all three ordered strings. The compressed seal is
authenticated before decryption/decompression. Neither command has an alternate
key path; the old flag-string-only final path is removed. The verifier requires
the **full** canonical verdict, then uses its membership decisions to filter
patrol edges, checks an actual total controller, and returns its normalized
submission flag. The memory budget alone cannot produce a flag.

The verifier checks safety and service order in each fixed-model product, then
removes service edges and tests for a reachable remaining cycle. Such a cycle
would permit an infinite no-service suffix. It does not union the environments,
count possible successful runs, or merely inspect the goal union of an SCC.

The reference rejects missing, extra, permuted, duplicated, wrong-type,
non-ASCII, and incorrect keys, invalid ciphertext, tampering, incomplete
submissions, incorrect verdict bytes, invalid controller indices, empty proofs,
and queue-independent position policies. Its isolated CLI check copies only
the challenge distribution, accepts the complete submission, and rejects the
obsolete flag-string format. The informal proof is reviewed separately;
requiring nonempty prose is not advertised as machine certification.

The executable checks also distinguish these tempting wrong implementations:

| Wrong simplification | Separating evidence |
| --- | --- |
| Treat `HK cap KH` as `H union K` | `abAB` is outside both subgroups but in Veil |
| Drop one product order | `abAcBC` passes the one-order condition only |
| Omit Core subtraction | Nonidentity `r^6` is removed by Core |
| Test only exponent sums | All 36 Transport records pass; only 18 are identities |
| Substitute into an ambient DFA without reduction | `x->a,y->Ab` sends `xy` to `b` |
| Add implicit inverse walk edges | A sole directed `a` loop accepts `a*`, not `A` |
| Mask edges after cancellation | A toy `b,a,A` path disappears when its middle ID is false |
| Find one safe factorization | `bcBC` has both the safe and accusing pairs above |
| Ignore Transport's graph mask | `abAB` changes final acceptance when all IDs are retained |
| Approximate the language by finite samples | The constructive pumping certificate proves infinitely many survivors |
| Use an independent position rotor | Probe `XX`, serve `a`, input `X`, serve `b` violates cyclic order |
| Identify the model but ignore probe's queue effect | `XY` and `YX` identify the same model but leave different queues |
| Ignore objective progress when location belief repeats | Identity queue with successive owed jobs forces different positions |
| Claim a memory minimum from one table's size | The 12+2 residual separation covers arbitrary Mealy tables |

The algebra-only proposal was independently solved from public files in
**192.131719 seconds** and was rejected as sufficiently difficult. Review also
found a common-root CRT reduction and 22 individually invisible hearing-mask
toggles; these are not counted as extra difficulty. The first patrol candidate
allowed a model-independent rotor and had loose memory bounds, so it too was
rejected. The replacement adds joint noncommuting control and a tight structural
memory lower bound, rather than disguising more generators or inflating tables.

These changes **do not establish that frontier models cannot solve the final
challenge**. Once the reductions and invariant are known, verification remains
inexpensive. Actual adversarial attack outcomes must be reported separately
from mathematical correctness, word lengths, and automaton sizes.

An independent arena-derived checker, replayed by the supervisor, verified the
14-memory winner, all 66 known-profile separations, and all 24 comparison-versus-
known separations. Its 182 failed thirteen-state quotients are regressions only;
the universal minimum follows from the residual argument, not that restricted
search. The final integrated package has **not** undergone a fresh timed blind
attack; further attack work was stopped at the user's request.
