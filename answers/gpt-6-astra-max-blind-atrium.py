"""Organizer-only reference solution and regression checks. Do not distribute."""
from collections import deque
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "gpt-6-astra-max-blind-atrium"


def mask(states):
    return sum(1 << q for q in set(states))


def beliefs(data):
    groups = [mask(q for q, z in enumerate(data["obs"]) if z == i) for i in range(3)]
    return sorted(b for b in range(1, 1 << len(data["obs"])) if any(b & g == b for g in groups))


def lift(data, mode):
    """Track possible current states B and endpoints of still-owing paths O."""
    bs = beliefs(data)
    groups = [mask(q for q, z in enumerate(data["obs"]) if z == i) for i in range(3)]
    target = mask(data["target"])
    posts = {}
    for b in [0] + bs:
        for a in range(3):
            posts[b, a] = mask(r for q in range(len(data["obs"])) if b >> q & 1
                               for r in data["transitions"][q][a])
    initial = {b: (b, 0 if mode == "ward" else b & ~target) for b in bs}
    queue = deque(initial.values())
    graph = {}
    while queue:
        node = b, owed = queue.popleft()
        if node in graph:
            continue
        actions = []
        for a in range(3):
            after = posts[b, a]
            debt = posts[b if mode == "omega" and owed == 0 else owed, a] & ~target
            successors = frozenset((after & g, 0 if mode == "ward" else debt & g)
                                   for g in groups if after & g)
            actions.append(successors)
            queue.extend(successors - graph.keys())
        graph[node] = actions
    return initial, graph


def pre(graph, region):
    return {node for node, actions in graph.items() if any(succ <= region for succ in actions)}


def winning(graph, mode, good):
    if mode in ("ward", "once"):
        region = set(good)
        while True:
            step = region & pre(graph, region) if mode == "ward" else region | pre(graph, region)
            if step == region:
                return region
            region = step
    region = set(graph)
    while True:
        frontier = set()
        recurrent = good & pre(graph, region)
        while True:
            step = recurrent | (region & pre(graph, frontier))
            if step == frontier:
                break
            frontier = step
        if frontier == region:
            return region
        region = frontier


def solve_part(data, mode):
    initial, graph = lift(data, mode)
    bad = mask(data["bad"])
    good = {node for node in graph if (node[0] & bad == 0 if mode == "ward" else node[1] == 0)}
    region = winning(graph, mode, good)
    return [b for b in initial if initial[b] in region]


def subflag(name, result):
    body = "".join(f"{b:04x}\n" for b in sorted(result)).encode("ascii")
    return f"SUB{{{name}:{sha256(body).hexdigest()}}}"


def controller_wins(data, table, initial, targets, forbidden):
    """Check safety and absence of reachable cycles avoiding each target."""
    pending = [(q, 0) for q in initial]
    graph = {}
    while pending:
        node = q, memory = pending.pop()
        if node in graph:
            continue
        if q in forbidden:
            return False
        action, next_memory = table[3 * memory + data["obs"][q]]
        graph[node] = {(r, next_memory) for r in data["transitions"][q][action]}
        pending.extend(graph[node] - graph.keys())
    for target in targets:
        remaining = {node for node in graph if node[0] not in target}
        # Delete target vertices from the entire reachable product graph.
        while remaining:
            sinks = {node for node in remaining if not graph[node] & remaining}
            if not sinks:
                return False
            remaining -= sinks
    return True


def solve_controller(data, final):
    # Two states suffice for this instance; exhaust all one-state tables first.
    for size in (1, 2):
        choices = list(product(range(3), range(size)))
        for table in product(choices, repeat=3 * size):
            if controller_wins(data, table, final["initial"], final["targets"], final["forbidden"]):
                code = "".join(f"{'abc'[a]}{m}" for a, m in table)
                return size, code, table
    raise AssertionError("no winning controller with at most two memory states")


def rejected(function, *args):
    try:
        function(*args)
    except ValueError:
        return
    raise AssertionError("invalid input was accepted")


def self_test(data, flags, final, answer, verify):
    assert json.dumps(final, ensure_ascii=False).isascii()
    # Winning families are downward closed; check all 93 candidates from maxima.
    maxima = {
        "ward": [0x000b, 0x000c, 0x08b0, 0x2740],
        "once": [0x100f, 0x08b0, 0x2740],
        "omega": [0x100b, 0x100c, 0x08b0, 0x2740],
    }
    assert len(beliefs(data)) == 93
    for mode, tops in maxima.items():
        expected = [b for b in beliefs(data) if any(b & top == b for top in tops)]
        assert solve_part(data, mode) == expected

    # Requiring B to be contained in the target genuinely fails on this arena.
    initial, graph = lift(data, "ward")
    goal = mask(data["target"])
    for mode, count in (("once", 62), ("omega", 61)):
        region = winning(graph, mode, {node for node in graph if node[0] & goal == node[0]})
        naive = {b for b, node in initial.items() if node in region}
        assert len(naive) == count
        assert naive < set(solve_part(data, mode))

    # Unknown phase: every path visits infinitely often, but B stays mixed.
    toggle = {"obs": [0, 0], "transitions": [[[1]] * 3, [[0]] * 3], "target": [0], "bad": []}
    assert all(solve_part(toggle, mode) == [1, 2, 3] for mode in maxima)
    transient = {"obs": [0] * 3, "transitions": [[[1]] * 3, [[2]] * 3, [[2]] * 3],
                 "target": [1], "bad": []}
    assert 1 in solve_part(transient, "once") and solve_part(transient, "omega") == []
    # The SCC meets the target, but the adversary can stay on a non-target loop.
    trap = {"obs": [0, 0], "transitions": [[[1]] * 3, [[0, 1]] * 3]}
    assert not controller_wins(trap, [(0, 0)] * 3, [0], [[0]], [])
    # Constant beliefs can still require alternating actions, not belief-only memory.
    alternating = {"obs": [0] * 3, "transitions": [[[0, 1, 2]] * 3,
                   [[0], [1], [1]], [[2], [0], [2]]], "target": [0], "bad": []}
    assert 7 in solve_part(alternating, "once") and 7 in solve_part(alternating, "omega")
    assert controller_wins(alternating, [(0, 1)] * 3 + [(1, 0)] * 3, [0, 1, 2], [[0]], [])
    assert all(not controller_wins(alternating, [(a, 0)] * 3, [0, 1, 2], [[0]], []) for a in range(3))
    # Each hidden state has a safe action, but their union has no common safe action.
    conflict = {"obs": [0, 0, 1], "transitions": [[[0], [2], [2]], [[2], [1], [2]], [[2]] * 3],
                "target": [], "bad": [2]}
    assert solve_part(conflict, "ward") == [1, 2]

    assert answer == "FLAG{blind-atrium:2:a0b1b1c0c0a1}"
    verify["check_flag"](answer, final["answer_sha256"])
    seal = json.loads((CHALLENGE / "final.seal.json").read_text(encoding="utf-8"))
    corrupt_seals = [[], {}, {"ciphertext": 1, "tag": "00"},
                     {**seal, "tag": "\u3042"}, {**seal, "tag": "00" * 32},
                     {**seal, "ciphertext": ["00" + "".join(seal["ciphertext"])[2:]]}]
    for broken in corrupt_seals:
        rejected(verify["unlock"], flags, broken)
    wrong_keys = [None, {}, "abc", [], flags + flags[:1], flags[::-1], [flags[0]] * 3]
    for i in range(3):
        wrong_keys += [flags[:i] + flags[i + 1:]]
        for bad in (None, "\u3042", flags[i] + "x", "x" * 257):
            wrong_keys.append(flags[:i] + [bad] + flags[i + 1:])
    for keys in wrong_keys:
        rejected(verify["key_from_flags"], keys)
        rejected(verify["unlock"], keys, seal)

    # Test the isolated distribution. Temporary key files are removed afterward.
    with TemporaryDirectory(prefix="blind-atrium-test-") as directory:
        temp = Path(directory)
        distribution = temp / "challenge"
        shutil.copytree(CHALLENGE, distribution)
        script = str(distribution / "verify.py")
        keys_file = temp / "keys.json"

        def cli(*args, status=0):
            result = subprocess.run([sys.executable, "-B", script, *args], cwd=temp,
                                    text=True, capture_output=True, timeout=10)
            assert result.returncode == status, (args, result.stdout, result.stderr)
            assert "Traceback" not in result.stderr
            return result.stdout

        for mode, flag in zip(maxima, flags):
            assert cli("sub", mode, flag).strip() == "OK"
            cli("sub", mode, flag + "x", status=1)
        keys_file.write_text(json.dumps(flags), encoding="utf-8")
        assert json.loads(cli("open", str(keys_file))) == final
        assert cli("final", str(keys_file), answer).strip() == "OK"
        cli("final", str(keys_file), answer + "x", status=1)
        for keys in wrong_keys:
            keys_file.write_text(json.dumps(keys), encoding="utf-8")
            cli("open", str(keys_file), status=1)
            cli("final", str(keys_file), answer, status=1)
        keys_file.write_text("{", encoding="utf-8")
        cli("open", str(keys_file), status=1)
        cli("open", str(temp / "missing.json"), status=1)
        cli("sub", "ward", "\u3042", status=1)
        cli("sub", "unknown", "flag", status=2)
        cli(status=2)


def main():
    data = json.loads((CHALLENGE / "arena.json").read_text(encoding="utf-8"))
    assert len(data["obs"]) == len(data["transitions"]) == 15
    assert all(data["obs"].count(z) == 5 for z in range(3))
    assert all(len(row) == 3 and all(edge and len(set(edge)) == len(edge)
               and all(type(q) is int and 0 <= q < 15 for q in edge) for edge in row)
               for row in data["transitions"])
    flags = []
    for mode in ("ward", "once", "omega"):
        result = solve_part(data, mode)
        flag = subflag(mode, result)
        flags.append(flag)
        print(mode, len(result), flag)
    verify = runpy.run_path(str(CHALLENGE / "verify.py"))
    seal = json.loads((CHALLENGE / "final.seal.json").read_text(encoding="utf-8"))
    final = verify["unlock"](flags, seal)
    size, code, _ = solve_controller(data, final)
    answer = f"FLAG{{blind-atrium:{size}:{code}}}"
    self_test(data, flags, final, answer, verify)
    print(answer)
    print("All checks passed: 93 initial sets, minimal two-state controller, isolated CLI, invalid inputs, tampered seals.")


if __name__ == "__main__":
    main()
