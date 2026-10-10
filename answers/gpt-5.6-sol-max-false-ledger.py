"""Recompute every answer to The False Ledger with the standard library."""

import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path


NAME = "gpt-5.6-sol-max-false-ledger"
ROOT = Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / NAME
LEDGER = json.loads((CHALLENGE / "ledger.json").read_text(encoding="utf-8"))
ROWS = tuple((row["person"], row["seat"]) for row in LEDGER["rows"])
ZONES = LEDGER["zones"]
SIZE = len(ROWS)
FULL = (1 << SIZE) - 1


@lru_cache(maxsize=None)
def valid(mask):
    people = set()
    seats = set()
    for index, (person, seat) in enumerate(ROWS):
        if mask & (1 << index):
            if person in people or seat in seats:
                return False
            people.add(person)
            seats.add(seat)
    return True


@lru_cache(maxsize=None)
def q0(mask):
    chosen = {
        person: [ZONES[seat] for index, (owner, seat) in enumerate(ROWS)
                 if owner == person and mask & (1 << index)]
        for person in ("A", "B", "C")
    }
    return any(
        zone_a == zone_c != zone_b
        for zone_a in chosen["A"]
        for zone_b in chosen["B"]
        for zone_c in chosen["C"]
    )


VALID = tuple(mask for mask in range(FULL + 1) if valid(mask))
EXTENSIONS = {
    mask: sum(
        1 << index
        for index in range(SIZE)
        if not mask & (1 << index) and valid(mask | (1 << index))
    )
    for mask in VALID
}


@lru_cache(maxsize=None)
def repairs(universe):
    return tuple(
        mask
        for mask in VALID
        if not mask & ~universe and not EXTENSIONS[mask] & universe
    )


def digest_masks(masks):
    data = "".join(f"{mask:04x}\n" for mask in masks).encode("ascii")
    return hashlib.sha256(data).hexdigest()


def sub_flag(name, masks):
    return f"SUB{{{name}:{len(masks)}:{digest_masks(masks)}}}"


def load_verifier():
    spec = importlib.util.spec_from_file_location("false_ledger_verify", CHALLENGE / "verify.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_rejection(action):
    try:
        action()
    except ValueError:
        return
    raise AssertionError("Invalid input was accepted")


def main():
    assert SIZE == 14
    assert [row["id"] for row in LEDGER["rows"]] == [f"t{i:02d}" for i in range(SIZE)]
    assert len(VALID) == 148

    repair_masks = repairs(FULL)
    lineage_masks = tuple(
        mask
        for mask in range(FULL + 1)
        if q0(mask)
        and all(not q0(mask ^ (1 << index)) for index in range(SIZE) if mask & (1 << index))
    )
    reassuring_masks = tuple(
        deleted
        for deleted in range(FULL + 1)
        if all(q0(repair) for repair in repairs(FULL ^ deleted))
    )
    flags = [
        sub_flag("repair", repair_masks),
        sub_flag("lineage", lineage_masks),
        sub_flag("reassure", reassuring_masks),
    ]

    verifier = load_verifier()
    for name, flag in zip(verifier.PARTS, flags):
        verifier.check_flag(flag, verifier.PARTS[name])

    seal = json.loads((CHALLENGE / "final.seal.json").read_text(encoding="utf-8"))
    task = verifier.unlock(flags, seal)
    if set(task) != {"query", "weights"}:
        raise ValueError("Unexpected final task")
    query = task["query"]
    weights = task["weights"]
    if (
        not isinstance(query, dict)
        or query.get("name") != "Q1"
        or query.get("zone_relation") != "equal"
        or not isinstance(query.get("persons"), list)
        or len(query["persons"]) != 2
        or not isinstance(weights, list)
        or len(weights) != SIZE
        or not all(isinstance(weight, int) and not isinstance(weight, bool) and weight > 0 for weight in weights)
    ):
        raise ValueError("Unexpected final task")
    first, second = query["persons"]

    @lru_cache(maxsize=None)
    def q1(mask):
        first_zones = [
            ZONES[seat]
            for index, (person, seat) in enumerate(ROWS)
            if person == first and mask & (1 << index)
        ]
        second_zones = [
            ZONES[seat]
            for index, (person, seat) in enumerate(ROWS)
            if person == second and mask & (1 << index)
        ]
        return any(left == right for left in first_zones for right in second_zones)

    feasible = tuple(
        deleted
        for deleted in range(FULL + 1)
        if all(q0(repair) and not q1(repair) for repair in repairs(FULL ^ deleted))
    )
    cost = lambda mask: sum(weights[index] for index in range(SIZE) if mask & (1 << index))
    best = min(feasible, key=lambda mask: (cost(mask), mask))
    final_flag = (
        f"FLAG{{false-ledger:{len(feasible)}:{cost(best)}:{best:04x}:"
        f"{digest_masks(feasible)}}}"
    )
    verifier.check_flag(final_flag, verifier.FINAL)

    assert sum(mask.bit_count() == 3 for mask in repair_masks) == 8
    assert sum(mask.bit_count() == 4 for mask in repair_masks) == 14
    assert sum(valid(mask) for mask in lineage_masks) == 6
    assert 0x1B9C in reassuring_masks and 0x1B9D not in reassuring_masks
    assert len(feasible) == 12 and best == 0x1F9C and cost(best) == 19

    expect_rejection(lambda: verifier.check_flag(flags[0] + "x", verifier.PARTS["repair"]))
    bad_seal = dict(seal)
    bad_seal["tag"] = ("0" if seal["tag"][0] != "0" else "1") + seal["tag"][1:]
    expect_rejection(lambda: verifier.unlock(flags, bad_seal))

    print(*flags, final_flag, sep="\n")


if __name__ == "__main__":
    main()
