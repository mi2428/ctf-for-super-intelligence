"""Organizer-only solver and executable checks. Do not distribute."""
from collections import deque
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "gpt-6.1-sol-max-folded-tribunal"
BASE = "aAbBcC"
SOURCE = "xXyYzZ"


def inverse(word):
    return word.swapcase()[::-1]


def reduce(word):
    stack = []
    for letter in word:
        if stack and stack[-1] == letter.swapcase():
            stack.pop()
        else:
            stack.append(letter)
    return "".join(stack)


def expand(word, images):
    table = dict(zip(SOURCE[::2], images))
    table.update({letter.swapcase(): inverse(image) for letter, image in list(table.items())})
    return reduce("".join(table[letter] for letter in word))


def marked_fold(basis):
    """Fold a based bouquet, retaining its inverse original-basis marking."""
    edges, next_vertex = [], 1
    for index, word in enumerate(basis):
        assert word and reduce(word) == word and set(word) <= set(BASE)
        vertex = 0
        for position, letter in enumerate(word):
            target = 0 if position == len(word) - 1 else next_vertex
            next_vertex += target != 0
            mark = SOURCE[2 * index] if target == 0 else ""
            edges.extend(((vertex, letter, target, mark), (target, letter.swapcase(), vertex, inverse(mark))))
            vertex = target
    while True:
        seen, unique, collision = {}, [], None
        for edge in edges:
            u, letter, v, mark = edge
            if (u, letter) in seen:
                previous = seen[u, letter]
                if previous[2] != v:
                    collision = previous, edge
                    break
                assert previous[3] == mark, "The supplied tuple is not a free basis"
            else:
                seen[u, letter] = edge
                unique.append(edge)
        if collision is None:
            edges = unique
            break
        first, second = collision
        if second[2] == 0:
            first, second = second, first
        keep, discard = first[2], second[2]
        gauge = reduce(inverse(first[3]) + second[3])
        edges = [
            (keep if u == discard else u, letter, keep if v == discard else v,
             reduce((gauge if u == discard else "") + mark + (inverse(gauge) if v == discard else "")))
            for u, letter, v, mark in edges
        ]
    raw = {(u, letter): (v, mark) for u, letter, v, mark in edges}
    numbers, tree_marks, queue = {0: 0}, {0: ""}, deque([0])
    while queue:
        u = queue.popleft()
        for letter in BASE:
            if (u, letter) in raw:
                v, mark = raw[u, letter]
                if v not in numbers:
                    numbers[v] = len(numbers)
                    tree_marks[v] = reduce(tree_marks[u] + mark)
                    queue.append(v)
    graph = [dict() for _ in numbers]
    for (u, letter), (v, mark) in raw.items():
        graph[numbers[u]][letter] = (numbers[v], reduce(tree_marks[u] + mark + inverse(tree_marks[v])))
    assert sum(map(len, graph)) // 2 - len(graph) + 1 == len(basis)
    for index, word in enumerate(basis):
        assert rewrite(graph, word) == SOURCE[2 * index]
    for u, row in enumerate(graph):
        for letter, (v, mark) in row.items():
            assert graph[v][letter.swapcase()] == (u, inverse(mark))
    return graph


def rewrite(graph, word):
    vertex, marks = 0, []
    for letter in reduce(word):
        if letter not in graph[vertex]:
            return None
        vertex, mark = graph[vertex][letter]
        marks.append(mark)
    return reduce("".join(marks)) if vertex == 0 else None


def add_word(nfa, start, word, end):
    for position, letter in enumerate(word):
        target = end if position == len(word) - 1 else len(nfa)
        if target == len(nfa):
            nfa.append({})
        nfa[start].setdefault(letter, set()).add(target)
        start = target
    if not word:
        nfa[start].setdefault("", set()).add(end)


def graph_nfa(graph):
    return [{letter: {target} for letter, (target, _) in row.items()} for row in graph]


def trim(nfa, finals):
    backwards = [set() for _ in nfa]
    for u, row in enumerate(nfa):
        for targets in row.values():
            for v in targets:
                backwards[v].add(u)
    live, queue = set(finals), deque(finals)
    while queue:
        for predecessor in backwards[queue.popleft()]:
            if predecessor not in live:
                live.add(predecessor)
                queue.append(predecessor)
    if 0 not in live:
        return [{}], set()
    order = [0] + sorted(live - {0})
    numbers = {old: new for new, old in enumerate(order)}
    return [
        {letter: {numbers[v] for v in targets if v in live}
         for letter, targets in nfa[u].items() if targets & live}
        for u in order
    ], {numbers[v] for v in finals}


def saturation(nfa, alphabet):
    """Benois closure: add epsilon paths for every cancellable inverse pair."""
    epsilon = [{i} | row.get("", set()) for i, row in enumerate(nfa)]
    changed = True
    while changed:
        changed = False
        for i in range(len(nfa)):
            reachable = set(epsilon[i])
            for j in tuple(epsilon[i]):
                reachable.update(epsilon[j])
            for letter in alphabet:
                for first in nfa[i].get(letter, ()):
                    for middle in epsilon[first]:
                        reachable.update(nfa[middle].get(letter.swapcase(), ()))
            if reachable != epsilon[i]:
                epsilon[i] = reachable
                changed = True
    return epsilon


def determinize(nfa, finals, alphabet, epsilon):
    start = frozenset(epsilon[0])
    states, numbers, transitions, accepting = [start], {start: 0}, [], []
    for subset in states:
        accepting.append(bool(subset & finals))
        row = []
        for letter in alphabet:
            targets = frozenset(
                target for u in subset for v in nfa[u].get(letter, ()) for target in epsilon[v]
            )
            if targets not in numbers:
                numbers[targets] = len(states)
                states.append(targets)
            row.append(numbers[targets])
        transitions.append(tuple(row))
    return transitions, accepting


def minimize(dfa):
    transitions, accepting = dfa
    classes = [int(value) for value in accepting]
    while True:
        signatures, refined = {}, []
        for i, row in enumerate(transitions):
            key = accepting[i], tuple(classes[target] for target in row)
            refined.append(signatures.setdefault(key, len(signatures)))
        if refined == classes:
            break
        classes = refined
    representatives = {block: i for i, block in reversed(list(enumerate(classes)))}
    order, numbers = [classes[0]], {classes[0]: 0}
    result, output_accepting = [], []
    for block in order:
        representative = representatives[block]
        row = []
        for target in transitions[representative]:
            next_block = classes[target]
            if next_block not in numbers:
                numbers[next_block] = len(order)
                order.append(next_block)
            row.append(numbers[next_block])
        result.append(tuple(row))
        output_accepting.append(bool(accepting[representative]))
    return result, output_accepting


def boolean(left, right, predicate):
    pairs, numbers, transitions, accepting = [(0, 0)], {(0, 0): 0}, [], []
    for u, v in pairs:
        accepting.append(bool(predicate(left[1][u], right[1][v])))
        row = []
        for a, b in zip(left[0][u], right[0][v]):
            pair = a, b
            if pair not in numbers:
                numbers[pair] = len(pairs)
                pairs.append(pair)
            row.append(numbers[pair])
        transitions.append(tuple(row))
    return minimize((transitions, accepting))


def reduced_dfa(alphabet):
    n, dead = len(alphabet), len(alphabet) + 1
    rows = [tuple(range(1, n + 1))]
    rows.extend(
        tuple(dead if letter == previous.swapcase() else alphabet.index(letter) + 1 for letter in alphabet)
        for previous in alphabet
    )
    rows.append((dead,) * n)
    return rows, [True] * (n + 1) + [False]


def language(nfa, finals, alphabet=BASE):
    nfa, finals = trim(nfa, finals)
    dfa = determinize(nfa, finals, alphabet, saturation(nfa, alphabet))
    return boolean(dfa, reduced_dfa(alphabet), lambda a, b: a and b)


def subgroup(graph):
    return language(graph_nfa(graph), {0})


def product_language(left, right):
    first, second = graph_nfa(left), graph_nfa(right)
    offset = len(first)
    first.extend({letter: {v + offset for v in targets} for letter, targets in row.items()} for row in second)
    first[0].setdefault("", set()).add(offset)
    return language(first, {offset})


def concatenate(left, right):
    first = [{BASE[i]: {target} for i, target in enumerate(row)} for row in left[0]]
    offset = len(first)
    first.extend({BASE[i]: {target + offset} for i, target in enumerate(row)} for row in right[0])
    for state, accepting in enumerate(left[1]):
        if accepting:
            first[state][""] = {offset}
    finals = {state + offset for state, accepting in enumerate(right[1]) if accepting}
    return language(first, finals)


def image_language(dfa, basis):
    nfa = [{} for _ in dfa[0]]
    for state, row in enumerate(dfa[0]):
        for letter, target in zip(SOURCE, row):
            add_word(nfa, state, expand(letter, basis), target)
    return language(nfa, {i for i, accepting in enumerate(dfa[1]) if accepting})


def pullback(dfa, graph):
    pairs, numbers, edges, finals = [(0, 0)], {(0, 0): 0}, [], set()
    for u, v in pairs:
        start = numbers[u, v]
        if dfa[1][u] and v == 0:
            finals.add(start)
        for letter, (target, mark) in graph[v].items():
            pair = dfa[0][u][BASE.index(letter)], target
            if pair not in numbers:
                numbers[pair] = len(pairs)
                pairs.append(pair)
            edges.append((start, mark, numbers[pair]))
    nfa = [{} for _ in pairs]
    for start, mark, end in edges:
        add_word(nfa, start, mark, end)
    return language(nfa, finals, SOURCE)


def silent(word, bases, graphs):
    maps = {"t": ("U", "V"), "T": ("V", "U"), "s": ("P", "Q"), "S": ("Q", "P")}
    powers, stable = [""], []
    for letter in word:
        if letter in BASE:
            powers[-1] += letter
        else:
            assert letter in maps
            stable.append(letter)
            powers.append("")
    powers = list(map(reduce, powers))
    while True:
        for i in range(len(stable) - 1):
            if stable[i + 1] != stable[i].swapcase():
                continue
            domain, codomain = maps[stable[i]]
            preimage = rewrite(graphs[domain], powers[i + 1])
            if preimage is not None:
                image = expand(preimage, bases[codomain])
                powers[i:i + 3] = [reduce(powers[i] + image + powers[i + 2])]
                stable[i:i + 2] = []
                break
        else:
            return not stable and powers == [""]


def recording(dfa, alphabet):
    transitions, accepting = dfa
    return ("alphabet=" + alphabet + "\n" + "".join(
        f"{i}:{int(accepting[i])}:" + ",".join(map(str, row)) + "\n"
        for i, row in enumerate(transitions)
    )).encode("ascii")


def automaton_flag(name, dfa, alphabet=BASE, final=False):
    return f"{'FLAG' if final else 'SUB'}{{{name}:{len(dfa[0])}:{sha256(recording(dfa, alphabet)).hexdigest()}}}"


def set_flag(name, rows):
    rows = sorted(set(rows))
    payload = "".join(row + "\n" for row in rows).encode("ascii")
    return f"SUB{{{name}:{len(rows)}:{sha256(payload).hexdigest()}}}"


def walk_language(score, identity_ids):
    nfa = [{} for _ in range(score["vertices"])]
    for edge in score["edges"]:
        if edge["id"] in identity_ids:
            add_word(nfa, edge["from"], edge["label"], edge["to"])
    return language(nfa, set(score["accepting"]))


def verdict(veil, paths, bases, graphs):
    # An accusing HK factorization exists exactly in A B; a KH one in B A.
    a = image_language(pullback(paths, graphs["V"]), bases["U"])
    b = image_language(pullback(paths, graphs["U"]), bases["V"])
    accusations = boolean(concatenate(a, b), concatenate(b, a), lambda x, y: x or y)
    return boolean(veil, accusations, lambda x, y: x and not y), a, b


def accepts(dfa, word, alphabet=BASE):
    state = 0
    for letter in word:
        state = dfa[0][state][alphabet.index(letter)]
    return dfa[1][state]


def witness(dfa):
    prefixes = {0: ""}
    queue = deque([0])
    while queue:
        state = queue.popleft()
        if dfa[1][state]:
            return prefixes[state]
        for letter, target in zip(BASE, dfa[0][state]):
            if target not in prefixes:
                prefixes[target] = prefixes[state] + letter
                queue.append(target)
    return None


def pumping_witness(dfa):
    """A reachable, coaccessible directed cycle proves an infinite language."""
    reverse = [[] for _ in dfa[0]]
    prefixes, queue = {0: ""}, deque([0])
    while queue:
        state = queue.popleft()
        for letter, target in zip(BASE, dfa[0][state]):
            reverse[target].append((state, letter))
            if target not in prefixes:
                prefixes[target] = prefixes[state] + letter
                queue.append(target)
    suffixes = {i: "" for i, accepting in enumerate(dfa[1]) if accepting}
    queue = deque(suffixes)
    while queue:
        state = queue.popleft()
        for predecessor, letter in reverse[state]:
            if predecessor not in suffixes:
                suffixes[predecessor] = letter + suffixes[state]
                queue.append(predecessor)
    if 0 not in suffixes:
        return None
    stack, active, finished, letters = [[0, 0]], {0: 0}, set(), []
    while stack:
        state, index = stack[-1]
        if index == len(BASE):
            finished.add(state)
            del active[state]
            stack.pop()
            if letters:
                letters.pop()
            continue
        stack[-1][1] += 1
        target, letter = dfa[0][state][index], BASE[index]
        if target not in suffixes or target in finished:
            continue
        if target in active:
            loop = "".join(letters[active[target]:]) + letter
            result = prefixes[target], loop, suffixes[target]
            assert all(accepts(dfa, result[0] + loop * n + result[2]) for n in range(3))
            return result
        active[target] = len(stack)
        letters.append(letter)
        stack.append([target, 0])
    return None


def solve(data):
    bases = data["bases"]
    graphs = {name: marked_fold(words) for name, words in bases.items()}
    h, k = graphs["U"], graphs["V"]
    core = boolean(subgroup(h), subgroup(k), lambda a, b: a and b)
    overlap = boolean(product_language(h, k), product_language(k, h), lambda a, b: a and b)
    veil = boolean(overlap, core, lambda a, b: a and not b)
    identities = {item["id"] for item in data["transport"] if silent(item["word"], bases, graphs)}
    return graphs, core, veil, identities


def self_check():
    assert reduce("aBbA") == "" and inverse("abC") == "cBA"
    basis = ["abA", "baB", "c"]
    graph = marked_fold(basis)
    for word in ("", "xyXzYY", "xYZXyz", "xyzXYZ"):
        assert rewrite(graph, expand(word, basis)) == reduce(word)
    assert rewrite(graph, "a") is None
    # Small explicit languages test cancellation, product order, and minimality.
    aa = [{"a": {0}, "A": {0}}]
    bb = [{"b": {0}, "B": {0}}]
    nfa = [{"a": {0}, "A": {0}, "": {1}}, {"b": {1}, "B": {1}}]
    ab = language(nfa, {1})
    assert accepts(ab, "aaBBB") and accepts(ab, "") and not accepts(ab, "ba")
    assert not accepts(ab, "aA") and accepts(language(aa, {0}), "AAA")
    assert len(language([{}], set())[0]) == 1
    assert len(language([{}], {0})[0]) == 2
    cancel = [{"a": {1}}, {"b": {2}}, {"B": {3}}, {"A": {4}}, {}]
    assert language(cancel, {4}) == language([{}], {0})
    assert language(bb, {0}) != language(aa, {0})
    preimage = pullback(subgroup(graph), graph)
    assert preimage == minimize(reduced_dfa(SOURCE))
    assert minimize(ab) == ab
    one_b = language([{"b": {1}}, {}], {1})
    cancellation_basis = ["a", "Ab", "c"]
    pulled = pullback(one_b, marked_fold(cancellation_basis))
    assert accepts(pulled, "xy", SOURCE) and not accepts(pulled, "y", SOURCE)
    assert image_language(pulled, cancellation_basis) == one_b
    assert recording(language([{}], {0}), BASE) == (
        b"alphabet=aAbBcC\n0:1:1,1,1,1,1,1\n1:0:1,1,1,1,1,1\n"
    )
    directed = {"vertices": 1, "accepting": [0], "edges": [{"id": "01", "from": 0, "to": 0, "label": "a"}]}
    assert accepts(walk_language(directed, {"01"}), "aaa")
    assert not accepts(walk_language(directed, {"01"}), "A")
    masked = {"vertices": 4, "accepting": [3], "edges": [
        {"id": "01", "from": 0, "to": 1, "label": "b"},
        {"id": "00", "from": 1, "to": 2, "label": "a"},
        {"id": "02", "from": 2, "to": 3, "label": "A"},
    ]}
    assert witness(walk_language(masked, {"01", "02"})) is None
    assert accepts(walk_language(masked, {"00", "01", "02"}), "b")


def rejection_checks(verifier, flags, seal, submission):
    def rejected(action):
        try:
            action()
        except ValueError:
            return
        raise AssertionError("Invalid input was accepted")

    for bad in ([], flags[:-1], flags[::-1], [flags[0]] * 3, flags + [flags[0]], [None] * 3, "keys", {}):
        rejected(lambda bad=bad: verifier["check_final"](bad, seal, submission))
    for bad in (None, 7, "é", [], {}, "FLAG{old-format}", dict(submission, proof=""),
                dict(submission, verdict=submission["verdict"] + "\n"),
                dict(submission, controller={"initial": False, "table": submission["controller"]["table"]}),
                dict(submission, controller={"initial": 0, "table": []})):
        rejected(lambda bad=bad: verifier["check_final"](flags, seal, bad))
    for broken in (
        {}, dict(seal, extra=1), dict(seal, tag="0" * 64), dict(seal, tag=None),
        dict(seal, ciphertext=[]), dict(seal, ciphertext=[None]),
        dict(seal, ciphertext=["zz"]), dict(seal, ciphertext=["0"]),
        dict(seal, ciphertext=["AA"]), dict(seal, ciphertext=[" "]),
        dict(seal, ciphertext=[("0" if seal["ciphertext"][0][0] != "0" else "1") + seal["ciphertext"][0][1:]] + seal["ciphertext"][1:]),
    ):
        rejected(lambda broken=broken: verifier["unlock"](flags, broken))
    sample, key = bytes(range(97)), bytes(range(32))
    assert verifier["xor_stream"](verifier["xor_stream"](sample, key), key) == sample


def swap_queue(q, theta, letter):
    i, j = ((0, 1), (1, 2))[theta ^ (letter == "Y")]
    q = list(q)
    q[i], q[j] = q[j], q[i]
    return tuple(q)


def advance_queue(q):
    return tuple((value - 1) % 3 for value in q)


def probe_queue(theta, first, second):
    return swap_queue(swap_queue((0, 1, 2), theta, first), theta, second)


def patrol_controller():
    roles = [(theta, q) for theta in range(2) for q in permutations(range(3))]
    numbers = {role: i for i, role in enumerate(roles)}
    rows = []
    for theta, q in roles:
        rows.append([[q.index(0), numbers[theta, advance_queue(q)]],
                     [3, numbers[theta, swap_queue(q, theta, "X")]],
                     [3, numbers[theta, swap_queue(q, theta, "Y")]], [3, numbers[theta, q]]])
    rows.append([[3, 12], [3, 12], [3, 13], [3, numbers[0, (0, 1, 2)]]])
    rows.append([[3, 12], [3, numbers[1, probe_queue(1, "Y", "X")]], [3, 12],
                 [3, numbers[1, probe_queue(1, "X", "Y")]]])
    return {"initial": 12, "table": rows}


def patrol_lower_bound(patrol, verdict, verifier):
    models = verifier["enabled_models"](patrol, verdict)
    permutations3 = list(permutations(range(3)))
    token = lambda q: "".join(map(str, q))
    for theta, (starts, unsafe, states) in enumerate(models):
        assert starts == ["P"] and unsafe == {"D"} and len(states) == 43 + theta
        for q in permutations3:
            suffix = token(q)
            observation, rows = states["H" + suffix]
            assert observation == 0 and rows["p"] == [("D", None)]
            for position, action in enumerate("abc"):
                assert set(rows[action]) == {("I1" + letter + token(swap_queue(q, theta, letter)), q[position]) for letter in "XY"}
            assert states["Z" + suffix][0] == 3 and states["Z" + suffix][1]["p"] == [("H" + suffix, None)]
            for letter in "XY":
                assert states["I1" + letter + suffix][0] == "HXYZ".index(letter)
                assert set(states["I1" + letter + suffix][1]["p"]) == {("Z" + suffix, None)} | {
                    ("I2" + other + token(swap_queue(q, theta, other)), None) for other in "XY"}
                assert states["I2" + letter + suffix][1]["p"] == [("Z" + suffix, None)]
        assert states["P"][1]["p"] == [("P1X", None), ("P1Y", None)]
        for first in "XY":
            second = first if theta == 0 else ("Y" if first == "X" else "X")
            assert states["P1" + first][0] == "HXYZ".index(first)
            assert states["P2" + first][0] == "HXYZ".index(second)
            assert states["P1" + first][1]["p"] == [("P2" + first, None)]
            result = token(probe_queue(theta, first, second))
            assert states["P2" + first][1]["p"] == [("PZ" + result, None)]
            assert states["PZ" + result][1]["p"] == [("H" + result, None)]
        for q, (observation, rows) in states.items():
            allowed = set("abc") if q.startswith("H") else {"p"}
            if q == "D":
                allowed = set()
            for action in set("abcp") - allowed:
                assert rows[action] == [("D", None)]
    roles = [(theta, q) for theta in range(2) for q in permutations3]
    words = ("X", "Y", "XX", "XY", "YX", "YY")

    def step(role, word):
        theta, q = role
        for letter in word:
            q = swap_queue(q, theta, letter)
        return q.index(0), (theta, advance_queue(q))

    separators = {}
    for i, left in enumerate(roles):
        reachable, queue = {left}, deque([left])
        while queue:
            current = queue.popleft()
            for word in words:
                target = step(current, word)[1]
                if target not in reachable:
                    reachable.add(target)
                    queue.append(target)
        assert len(reachable) == 6
        for right in roles[:i]:
            queue, seen, found = deque([((left, right), [])]), {(left, right)}, None
            while queue and found is None:
                (a, b), prefix = queue.popleft()
                for word in words:
                    output_a, next_a = step(a, word)
                    output_b, next_b = step(b, word)
                    if output_a != output_b:
                        found = prefix + [word]
                        break
                    pair = next_a, next_b
                    if pair not in seen:
                        seen.add(pair)
                        queue.append((pair, prefix + [word]))
            assert found is not None, (left, right)
            separators[left, right] = found
    # Probe comparisons identify different fixed models on a common second reply.
    for first in "XY":
        for theta, q in roles:
            second = first if theta == 1 else ("Y" if first == "X" else "X")
            probe_theta = int(first != second)
            assert probe_theta != theta
            after_probe = probe_theta, advance_queue(probe_queue(probe_theta, first, second))
            after_known = theta, advance_queue(swap_queue(q, theta, second))
            assert (after_probe, after_known) in separators or (after_known, after_probe) in separators
    assert len(separators) == 66 and max(map(len, separators.values())) == 2
    return 12 + 2


def isolated_cli(flags, submission, final):
    with TemporaryDirectory(prefix=".folded-tribunal-check-", dir=ROOT) as directory:
        temp = Path(directory)
        distribution = temp / "challenge"
        shutil.copytree(CHALLENGE, distribution)
        keys, answer = temp / "keys.json", temp / "submission.json"
        keys.write_text(json.dumps(flags), encoding="utf-8")
        answer.write_text(json.dumps(submission), encoding="utf-8")

        def cli(*args, status=0):
            result = subprocess.run([sys.executable, "-B", str(distribution / "verify.py"), *args],
                                    cwd=temp, text=True, capture_output=True, timeout=10)
            assert result.returncode == status, (args, result.stdout, result.stderr)
            assert "Traceback" not in result.stderr
            return result.stdout

        for name, flag in zip(("core", "veil", "transport"), flags):
            assert cli("sub", name, flag).strip() == "OK"
            cli("sub", name, flag + "x", status=1)
        assert "patrol" in json.loads(cli("open", str(keys)))
        assert cli("final", str(keys), str(answer)).splitlines() == ["OK", final]
        for bad in ([], flags[:-1], flags[::-1], [flags[0]] * 3, [None] * 3):
            keys.write_text(json.dumps(bad), encoding="utf-8")
            cli("open", str(keys), status=1)
            cli("final", str(keys), str(answer), status=1)
        keys.write_text(json.dumps(flags), encoding="utf-8")
        cli("final", str(keys), "FLAG{obsolete}", status=1)
        answer.write_text("{}", encoding="utf-8")
        cli("final", str(keys), str(answer), status=1)
        cli(status=2)


def instance_checks(data, graphs, core, veil, identities, score, paths, final_dfa, a, b):
    r = "abAB"
    h, k = subgroup(graphs["U"]), subgroup(graphs["V"])
    assert accepts(core, r * 6) and not accepts(veil, r * 6)
    assert accepts(veil, r) and not accepts(h, r) and not accepts(k, r)
    assert len(identities) == 18 and len(data["transport"]) == 36
    assert all(item["word"].count(letter) == item["word"].count(letter.swapcase())
               for item in data["transport"] for letter in "abcts")
    for stable, domain, codomain in (("t", "U", "V"), ("T", "V", "U"), ("s", "P", "Q"), ("S", "Q", "P")):
        for word in ("", "x", "X", "xyXzYY"):
            relation = stable + expand(word, data["bases"][domain]) + stable.swapcase() + inverse(expand(word, data["bases"][codomain]))
            assert silent(relation, data["bases"], graphs)
    assert not silent("tsTS", data["bases"], graphs)
    assert not silent("taTb tATB".replace(" ", ""), data["bases"], graphs)
    hk, kh = product_language(graphs["U"], graphs["V"]), product_language(graphs["V"], graphs["U"])
    one_order = boolean(boolean(hk, core, lambda x, y: x and not y), veil, lambda x, y: x and not y)
    lost_order = witness(one_order)
    assert lost_order is not None
    removed = witness(boolean(veil, final_dfa, lambda x, y: x and not y))
    assert removed is not None and witness(final_dfa) is not None
    safe_hk = boolean(
        concatenate(boolean(h, a, lambda x, y: x and not y), k),
        concatenate(h, boolean(k, b, lambda x, y: x and not y)), lambda x, y: x or y,
    )
    ambiguous = witness(boolean(boolean(safe_hk, concatenate(a, b), lambda x, y: x and y), veil, lambda x, y: x and y))
    assert ambiguous is not None
    # These actual decompositions certify the quantifier error without a length cutoff.
    certificates = {}
    p, q = "bcBC", "caCA"
    common = ["", r * 6, inverse(r * 6), reduce(r * 3 + p + inverse(r * 3)), reduce(r * 4 + q + inverse(r * 4))]
    common += [inverse(word) for word in common[1:]]
    for left in common:
        for right in common:
            j = reduce(left + right)
            assert accepts(core, j)
            h_word, k_word = j, reduce(inverse(j) + ambiguous)
            h_mark, k_mark = rewrite(graphs["U"], h_word), rewrite(graphs["V"], k_word)
            if h_mark is None or k_mark is None:
                continue
            assert reduce(h_word + k_word) == ambiguous
            bits = accepts(paths, expand(h_mark, data["bases"]["V"])), accepts(paths, expand(k_mark, data["bases"]["U"]))
            certificates.setdefault("accusing" if all(bits) else "safe", (h_word, k_word, bits))
    assert set(certificates) == {"safe", "accusing"}
    ignored_mask = walk_language(score, {item["id"] for item in data["transport"]})
    wrong_final, _, _ = verdict(veil, ignored_mask, data["bases"], graphs)
    mask_witness = witness(boolean(final_dfa, wrong_final, lambda x, y: x and not y))
    assert mask_witness is not None
    pump = pumping_witness(final_dfa)
    assert pump is not None
    assert all(not accepts(dfa, "aA") for dfa in (core, veil, paths, final_dfa))
    assert tuple(map(lambda dfa: len(dfa[0]), (core, veil, paths, a, b, final_dfa))) == (62, 190, 54, 268, 433, 1601)
    return {"one_order_error": lost_order, "removed_by_hearing": removed,
            "safe_and_accusing_HK": ambiguous, "mask_dependency": mask_witness,
            "factorizations": certificates, "infinite_family": pump}


def main():
    self_check()
    data = json.loads((CHALLENGE / "tribunal.json").read_text(encoding="utf-8"))
    graphs, core, veil, identities = solve(data)
    flags = [automaton_flag("core", core), automaton_flag("veil", veil), set_flag("transport", identities)]
    verifier = runpy.run_path(str(CHALLENGE / "verify.py"))
    seal = json.loads((CHALLENGE / "finale.seal.json").read_text(encoding="utf-8"))
    score = verifier["unlock"](flags, seal)
    paths = walk_language(score, identities)
    final_dfa, a, b = verdict(veil, paths, data["bases"], graphs)
    controller = patrol_controller()
    minimum = patrol_lower_bound(score["patrol"], final_dfa, verifier)
    assert minimum == len(controller["table"]) == score["patrol"]["memory_limit"] == 14
    submission = {"verdict": recording(final_dfa, BASE).decode("ascii"), "controller": controller,
                  "proof": "Use relative_queue[j]=(queue[j]-next_job)%3. A safe service advances its values; input letters swap its positions according to the fixed model. This gives twelve known profiles and two probe-comparison memories. Every winner is forced to serve the owed job and acknowledge inputs, so the six relative queues in each fixed model are all reachable. At the pre-input points, their forced-response residuals are pairwise distinct: all 66 pairs have legal separating segment sequences of at most two rounds. Neither first-probe comparison can share a known pre-input memory: choose the last reply consistent with the opposite fixed initial model, then Z,H and a separating known-profile continuation. The two comparisons are distinct on common reply X. Thus arbitrary winning Mealy controllers need 12+2 memories, including phase-aliasing alternatives; this construction uses fourteen."}
    final = verifier["check_final"](flags, seal, submission)
    assert final == "FLAG{folded-tribunal:14:ce38f2915f421da2020f10604fcf571bf795360f11cfdcafe20e831e7372cd81}"
    rejection_checks(verifier, flags, seal, submission)
    isolated_cli(flags, submission, final)
    wrong = json.loads(json.dumps(submission))
    for row in wrong["controller"]["table"][:12]:
        row[0][0] = 0
    try:
        verifier["check_final"](flags, seal, wrong)
    except ValueError:
        pass
    else:
        raise AssertionError("A queue-independent position strategy was accepted")
    witnesses = instance_checks(data, graphs, core, veil, identities, score, paths, final_dfa, a, b)
    print("\n".join(flags + [final]))
    print(f"Identity IDs: {','.join(sorted(identities))}")
    print(f"Graph vertices: { {name: len(graph) for name, graph in graphs.items()} }")
    print(f"DFA states: core={len(core[0])}, veil={len(veil[0])}, paths={len(paths[0])}, verdict={len(final_dfa[0])}")
    print(f"Patrol: minimum memory={minimum}; twelve known residuals + two probe comparisons")
    print("Witnesses: " + json.dumps(witnesses))
    print("Checks passed: exact infinite languages, marked transport, universal factorizations, tight patrol memory bound, isolated semantic CLI, gate rejection")


if __name__ == "__main__":
    main()
