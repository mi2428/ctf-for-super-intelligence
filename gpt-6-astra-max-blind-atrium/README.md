# Blind Atrium

> Everyone heard the bell. There was never a moment when everyone could be known to be at the bell.

Fifteen rooms. Three colors in the surveillance window.
Break the seals of **always**, **eventually**, and **infinitely often**. Then build the smallest controller.

## Distribution and rules

- Use only this directory: `arena.json` contains the arena, `final.seal.json` seals the final task, and `verify.py` checks submissions.
- Verification requires Python 3.10 or later and its standard library. No network, external references, or additional packages are needed.
- You may write programs and inspect the verifier. Brute-forcing hash commitments, modifying the distribution, and reading undistributed answers or Git history are not solutions.
- Collect **all three** sub-flags before opening the final task. Submit all sub-flags, the final flag, and a derivation.
- The state spaces are small. The difficulty is deciding what can be observed and what must hold on every possible play, not performing expensive computation.

## The common arena

Rooms, also called states, are the integers `0,...,14`. Actions are `a,b,c`. Observations are `0,1,2`.

- `obs[q]` is the observation of room `q`.
- `transitions[q][0]`, `[1]`, and `[2]` are the **sets** of possible destinations after actions `a,b,c`, respectively. List order has no meaning.
- `bad` is the set of dangerous rooms. `target` is the set of rooms containing a bell. Neither set has special transition rules.

Each trial starts with a specified, nonempty initial set `B`. All its members must have the same observation.
The controller knows the arena and `B`. The adversary selects `q₀ ∈ B`.
For each time `t = 0,1,2,...`, the following sequence repeats forever:

1. The controller receives **only** `zₜ = obs[qₜ]`.
2. It selects one action `aₜ` using its observation history `z₀,...,zₜ` and its own previous actions.
3. The adversary selects `qₜ₊₁` from the transition set for room `qₜ` and action `aₜ`.

The adversary knows the actual room and the controller's strategy, and may adapt to the past.
There is **no probability and no fairness assumption**. A play that forever ignores an available destination must still be handled.
Every transition set is nonempty, so every play is infinite.

The controller receives no room number, danger indicator, bell indicator, or notification of success.
It may use anything logically inferable from observations and its own actions. For the three sub-challenges, memory is unrestricted, but randomization is not allowed.

An initial set `B` is **winning** if:

**There exists one observation-history-based strategy for that `B` which wins for every initial room in `B` and every choice by the adversary.**

Choosing a different strategy for each hidden actual play is not allowed.
Different initial sets and different sub-challenges may use different strategies.
Time zero counts in every objective.

## I — Ward: always

Find **all** initial sets `B` from which the controller can guarantee:

```text
On every play, qₜ ∉ bad for every t ≥ 0.
```

## II — Once: eventually

Find **all** initial sets `B` from which the controller can guarantee:

```text
On every play, there exists a time t ≥ 0 with qₜ ∈ target.
```

The visiting time may differ between plays. There is no obligation to remain at the target or to detect the visit.
Entering `bad` does not, by itself, lose this sub-challenge.

## III — Omega: infinitely often

Find **all** initial sets `B` from which the controller can guarantee:

```text
On every play, {t ≥ 0 : qₜ ∈ target} is an infinite set.
```

Avoiding `bad` is not an additional requirement here either.
Neither arbitrarily many possible visits nor an infinite number of visits on just one possible play is sufficient.

## Encoding the sub-flags

Encode an initial set as the integer `m(B) = Σ(q∈B) 2^q`.
For **every** winning initial set, write its mask as exactly four lowercase hexadecimal digits, including leading zeroes.
Remove duplicates and sort in ascending numerical order. Append exactly one LF to every line, including the last.
Use zero bytes if there are no winning initial sets. Let `H` be the lowercase, 64-digit SHA-256 hexadecimal digest of these ASCII bytes.

For example, **if** the winning initial sets were exactly `{0}` and `{0,2}`, the bytes would be `b"0001\n0005\n"`.
This is only a formatting example, not a claim about the arena.
Do not include the empty initial set, mixed-observation initial sets, or losing initial sets.

The sub-flags are `SUB{ward:H}`, `SUB{once:H}`, and `SUB{omega:H}`, respectively.
Do not record only the inclusion-maximal winning sets.

## IV — The sealed controller

All three correct sub-flags are required to decrypt the final task.
It uses the same arena; its objective and submission format are revealed upon opening.
The seal merely enforces the stages. Breaking cryptography is not part of the challenge.

Run the following commands from this directory, replacing each `H` with the digest you obtained:

```sh
python3 -B verify.py sub ward 'SUB{ward:H}'
python3 -B verify.py sub once 'SUB{once:H}'
python3 -B verify.py sub omega 'SUB{omega:H}'
```

Put the three actual sub-flags into `keys.json` in **ward, once, omega** order.
The following is a template, not a set of valid keys:

```json
["SUB{ward:H}", "SUB{once:H}", "SUB{omega:H}"]
```

```sh
python3 -B verify.py open keys.json
python3 -B verify.py final keys.json 'YOUR_FINAL_FLAG'
```

Both `open` and `final` verify all three keys. Missing, incorrect, or reordered keys are rejected.
Success exits with status 0: `sub` and `final` print `OK`, while `open` prints the final task as JSON.
An incorrect answer or invalid file exits with status 1. Invalid command syntax exits with status 2.
