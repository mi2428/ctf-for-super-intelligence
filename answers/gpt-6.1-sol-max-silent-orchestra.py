"""Organizer-only reference solution and reproducibility check. Do not distribute."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import runpy


CHALLENGE = Path(__file__).resolve().parents[1] / "gpt-6.1-sol-max-silent-orchestra"


def flag(name, rows, final=False):
    rows = sorted(set(rows))
    payload = "".join(row + "\n" for row in rows).encode("ascii")
    return f"{'FLAG' if final else 'SUB'}{{{name}:{len(rows)}:{sha256(payload).hexdigest()}}}"


def solve_echo(data):
    deck = Counter(data["deck"])
    n = data["length"]
    assert sum(deck.values()) == n
    start = min(edge[:-1] for edge in deck)
    found = set()

    def walk(vertex, word, remaining):
        if not remaining:
            if vertex == start:
                word = word[:n]
                found.add(min(word[i:] + word[:i] for i in range(n)))
            return
        for bit in "01":
            edge = vertex + bit
            if deck[edge]:
                deck[edge] -= 1
                walk(edge[1:], word + bit, remaining - 1)
                deck[edge] += 1

    walk(start, start, n)
    return found


def moments(n, edges, bits, degree):
    neighbors = [[] for _ in range(n)]
    for (u, v), bit in zip(edges, bits):
        sign = 1 if bit == "0" else -1
        neighbors[u].append((v, sign))
        neighbors[v].append((u, sign))
    matrix = [[int(i == j) for j in range(n)] for i in range(n)]
    result = [n]
    for _ in range(degree):
        matrix = [
            [sum(row[k] * sign for k, sign in neighbors[j]) for j in range(n)]
            for row in matrix
        ]
        result.append(sum(matrix[i][i] for i in range(n)))
    return result


def solve_chamber(data):
    n, edges, target = data["vertices"], data["edges"], data["moments"]
    assert edges[:n - 1] == [[i, i + 1] for i in range(n - 1)]
    found = set()
    for chords in product("01", repeat=len(edges) - n + 1):
        bits = "0" * (n - 1) + "".join(chords)
        if moments(n, edges, bits, len(target) - 1) == target:
            found.add(bits)
    return found


def reduce_hnn(word):
    """Britton reduction: decide triviality without assuming a unique reduced form."""
    if set(word) - set("aAtT"):
        raise ValueError("Invalid letter in word")
    powers, stable = [0], []
    for letter in word:
        if letter in "aA":
            powers[-1] += 1 if letter == "a" else -1
        else:
            stable.append(1 if letter == "t" else -1)
            powers.append(0)
    while True:
        for i in range(len(stable) - 1):
            divisor, multiplier = (2, 3) if stable[i] == 1 else (3, 2)
            if stable[i] == -stable[i + 1] and powers[i + 1] % divisor == 0:
                value = powers[i + 1] // divisor * multiplier
                powers[i:i + 3] = [powers[i] + value + powers[i + 2]]
                stable[i:i + 2] = []
                break
        else:
            return tuple(powers), tuple(stable)


def silent(word):
    return reduce_hnn(word) == ((0,), ())


def affine(word):
    scale, offset = Fraction(1), Fraction(0)
    for letter in word:
        if letter in "aA":
            offset += scale if letter == "a" else -scale
        else:
            scale *= Fraction(3, 2) if letter == "t" else Fraction(2, 3)
    return scale, offset


def closed_scores(bars):
    bars = {bar["id"]: bar for bar in bars}
    anchor = bars["a"]
    found = []

    def visit(vertex, unused, order, word):
        if not unused:
            if vertex == anchor["in"]:
                found.append((order, word))
            return
        for name in sorted(unused):
            bar = bars[name]
            if bar["in"] == vertex:
                visit(bar["out"], unused - {name}, order + name, word + bar["word"])

    visit(anchor["out"], set(bars) - {"a"}, "a", anchor["word"])
    return found


def main():
    data = json.loads((CHALLENGE / "instruments.json").read_text(encoding="utf-8"))
    gate = runpy.run_path(str(CHALLENGE / "verify.py"))
    seal = json.loads((CHALLENGE / "finale.seal.json").read_text(encoding="utf-8"))
    echo = solve_echo(data["echo"])
    chamber = solve_chamber(data["chamber"])
    canon = {item["id"] for item in data["canon"] if silent(item["word"])}
    assert (len(echo), len(chamber), len(canon)) == (36, 11, 8)
    flags = [flag(name, rows) for name, rows in zip(("echo", "chamber", "canon"), (echo, chamber, canon))]
    finale = gate["unlock"](flags, seal)
    scores = closed_scores(finale["bars"])
    orders = {order for order, word in scores if silent(word)}
    assert len(scores) == 256 and len(orders) == 7
    assert all(affine(item["word"]) == (1, 0) for item in data["canon"])
    assert sum(affine(word) == (1, 0) for _, word in scores) == 19
    final = flag("silent-orchestra", orders, final=True)
    gate["check_final"](flags, seal, final)

    # Counterexamples and negative powers catch affine-map and divisibility mistakes.
    assert silent("tAATaaa") and silent("TAAAtaa")
    assert not silent("taTatATA") and affine("taTatATA") == (1, 0)
    assert flag("x", []) == "SUB{x:0:" + sha256(b"").hexdigest() + "}"
    sample, key = bytes(range(65)), bytes(range(32))
    assert gate["xor_stream"](gate["xor_stream"](sample, key), key) == sample

    bad_keys = [[], flags[:-1], flags[::-1], [flags[0]] * 3, flags + [flags[0]], [None] * 3]
    for bad in bad_keys:
        try:
            gate["check_final"](bad, seal, final)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid keys accepted the final flag")
    for broken in (
        dict(seal, tag="0" * 64),
        dict(seal, ciphertext=[("0" if seal["ciphertext"][0][0] != "0" else "1") + seal["ciphertext"][0][1:]] + seal["ciphertext"][1:]),
    ):
        try:
            gate["unlock"](flags, broken)
        except ValueError:
            pass
        else:
            raise AssertionError("A modified score seal was accepted")
    try:
        gate["check_final"](flags, seal, final + "x")
    except ValueError:
        pass
    else:
        raise AssertionError("An incorrect final flag was accepted")
    print("\n".join(flags + [final]))
    print("Checks passed: complete solution sets, affine counterexample, key rejection, seal authentication, final flag")


if __name__ == "__main__":
    main()
