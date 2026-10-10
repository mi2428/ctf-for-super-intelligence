"""Standard-library flag verifier; all three keys are required for the hearing."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import sys
import zlib


PARTS = {
    "core": "9dc2e276f0dc1f999364cd273addc111f7f22bd6a30486290e9bae9fa26158d5",
    "veil": "c194049b44a43b6455cec2670ae188921dc7a1d208c9557e04589dd7b880f956",
    "transport": "55ce2afa94e5e942a41f1fa11941da25b10a46ed97588d9e3c81ff32a072bbb4",
}
VERDICT_SHA256 = "4bec3213acadf240d27970a33915801465620e4d5363f45005a9a0ecf10fab46"
DOMAIN = b"folded-tribunal/"


def check_flag(flag, expected):
    if not isinstance(flag, str) or len(flag) > 256 or not flag.isascii():
        raise ValueError("A flag must be an ASCII string of at most 256 characters")
    if not hmac.compare_digest(hashlib.sha256(flag.encode("ascii")).hexdigest(), expected):
        raise ValueError("Flag mismatch")


def key_from_flags(flags):
    if not isinstance(flags, list) or len(flags) != 3:
        raise ValueError("Keys must be a three-element array in core, veil, transport order")
    for name, flag in zip(PARTS, flags):
        try:
            check_flag(flag, PARTS[name])
        except ValueError as error:
            raise ValueError(f"{name}: {error}") from error
    return hashlib.sha256(DOMAIN + b"keys/v2\0" + b"\0".join(flag.encode("ascii") for flag in flags)).digest()


def xor_stream(data, key):
    result = bytearray()
    for offset in range(0, len(data), 32):
        block = hashlib.sha256(DOMAIN + b"stream/v2\0" + key + (offset // 32).to_bytes(8, "big")).digest()
        result.extend(a ^ b for a, b in zip(data[offset:offset + 32], block))
    return bytes(result)


def unlock(flags, seal):
    key = key_from_flags(flags)
    if not isinstance(seal, dict) or set(seal) != {"ciphertext", "tag"}:
        raise ValueError("Invalid hearing seal format")
    chunks, tag = seal["ciphertext"], seal["tag"]
    if not isinstance(chunks, list) or not chunks or not all(isinstance(s, str) and s for s in chunks):
        raise ValueError("Invalid hearing seal format")
    if not isinstance(tag, str) or len(tag) != 64 or any(c not in "0123456789abcdef" for c in tag):
        raise ValueError("Invalid hearing seal format")
    encoded = "".join(chunks)
    if len(encoded) % 2 or any(c not in "0123456789abcdef" for c in encoded):
        raise ValueError("Invalid hearing ciphertext")
    ciphertext = bytes.fromhex(encoded)
    actual = hmac.new(key, DOMAIN + b"seal/v2\0" + ciphertext, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual, tag):
        raise ValueError("Hearing seal authentication failed")
    return json.loads(zlib.decompress(xor_stream(ciphertext, key)).decode("utf-8"))


def parse_verdict(text):
    if not isinstance(text, str) or not text.isascii() or len(text) > 1_000_000:
        raise ValueError("Verdict must be a canonical ASCII automaton recording")
    if not hmac.compare_digest(hashlib.sha256(text.encode("ascii")).hexdigest(), VERDICT_SHA256):
        raise ValueError("Incorrect verdict automaton")
    lines = text.splitlines()
    if not text.endswith("\n") or lines[0] != "alphabet=aAbBcC":
        raise ValueError("Invalid verdict recording")
    transitions, accepting = [], []
    for i, line in enumerate(lines[1:]):
        number, bit, targets = line.split(":")
        if number != str(i) or bit not in ("0", "1"):
            raise ValueError("Invalid verdict state")
        row = targets.split(",")
        if len(row) != 6 or any(not target.isdigit() or target != str(int(target)) for target in row):
            raise ValueError("Invalid verdict transition")
        transitions.append(list(map(int, row)))
        accepting.append(bit == "1")
    if any(not 0 <= target < len(transitions) for row in transitions for target in row):
        raise ValueError("Unknown verdict state")
    return transitions, accepting


def enabled_models(patrol, verdict):
    def allowed(word):
        state = 0
        for letter in word:
            state = verdict[0][state]["aAbBcC".index(letter)]
        return verdict[1][state]

    models = []
    for model in patrol["models"]:
        states = {}
        for q, state in model["states"].items():
            rows = {}
            for action, edges in state["transitions"].items():
                rows[action] = [(edge["to"], edge["event"]) for edge in edges if allowed(patrol["guards"][edge["guard"]])]
                if not rows[action]:
                    raise ValueError("An arena action has no enabled successor")
            states[q] = (patrol["observations"].index(state["observation"]), rows)
        models.append((model["starts"], set(model["unsafe"]), states))
    return models


def normalize_controller(controller, limit, observations, actions):
    if not isinstance(controller, dict) or set(controller) != {"initial", "table"}:
        raise ValueError("Controller must contain exactly initial and table")
    initial, table = controller["initial"], controller["table"]
    if not isinstance(table, list) or not 1 <= len(table) <= limit or type(initial) is not int or not 0 <= initial < len(table):
        raise ValueError("Invalid controller size or initial memory")
    for row in table:
        if not isinstance(row, list) or len(row) != observations:
            raise ValueError("Incomplete controller row")
        for cell in row:
            if not isinstance(cell, list) or len(cell) != 2 or any(type(value) is not int for value in cell):
                raise ValueError("Controller cells must be [action, next_memory] integer pairs")
            if not 0 <= cell[0] < actions or not 0 <= cell[1] < len(table):
                raise ValueError("Unknown controller action or memory")
    order, numbers = [initial], {initial: 0}
    for old in order:
        for _, target in table[old]:
            if target not in numbers:
                numbers[target] = len(order)
                order.append(target)
    if len(order) != len(table):
        raise ValueError("Controller contains unreachable memory states")
    return {"initial": 0, "table": [[[action, numbers[target]] for action, target in table[old]] for old in order]}


def controller_wins(patrol, models, controller):
    for starts, unsafe, states in models:
        pending = [(q, 0, 0) for q in starts]
        no_event = {}
        while pending:
            node = q, memory, expected = pending.pop()
            if node in no_event:
                continue
            if q in unsafe:
                raise ValueError("Controller can reach an unsafe state")
            observation, rows = states[q]
            action, updated = controller["table"][memory][observation]
            no_event[node] = set()
            for target, event in rows[patrol["actions"][action]]:
                if event is not None and event != expected:
                    raise ValueError("Controller can violate cyclic service order")
                following = target, updated, expected if event is None else (expected + 1) % 3
                if event is None:
                    no_event[node].add(following)
                pending.append(following)
        remaining = set(no_event)
        while remaining:
            sinks = {node for node in remaining if not no_event[node] & remaining}
            if not sinks:
                raise ValueError("Controller permits an infinite play with no further service")
            remaining -= sinks


def check_final(flags, seal, submission):
    score = unlock(flags, seal)
    if not isinstance(submission, dict) or set(submission) != {"verdict", "controller", "proof"}:
        raise ValueError("Submission must contain exactly verdict, controller, and proof")
    proof = submission["proof"]
    if not isinstance(proof, str) or not proof.strip() or len(proof) > 200_000:
        raise ValueError("A nonempty memory-minimality derivation is required")
    verdict = parse_verdict(submission["verdict"])
    patrol = score["patrol"]
    controller = normalize_controller(submission["controller"], patrol["memory_limit"], len(patrol["observations"]), len(patrol["actions"]))
    controller_wins(patrol, enabled_models(patrol, verdict), controller)
    # The prose derivation is reviewed by the organizer, not certified by this checker.
    record = (json.dumps(controller, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    digest = hashlib.sha256(DOMAIN + b"submission/v2\0" + submission["verdict"].encode("ascii") + b"\0" + record).hexdigest()
    return f"FLAG{{folded-tribunal:{len(controller['table'])}:{digest}}}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("sub", help="Check a sub-flag")
    sub.add_argument("part", choices=PARTS)
    sub.add_argument("flag")
    opening = commands.add_parser("open", help="Open the hearing with all three keys")
    opening.add_argument("keys", type=Path)
    final = commands.add_parser("final", help="Verify a full verdict/controller submission and all three keys")
    final.add_argument("keys", type=Path)
    final.add_argument("submission", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "sub":
            check_flag(args.flag, PARTS[args.part])
        else:
            flags = json.loads(args.keys.read_text(encoding="utf-8"))
            seal = json.loads(Path(__file__).with_name("finale.seal.json").read_text(encoding="utf-8"))
            if args.command == "open":
                print(json.dumps(unlock(flags, seal), ensure_ascii=False, indent=2))
                return 0
            submission = json.loads(args.submission.read_text(encoding="utf-8"))
            flag = check_final(flags, seal, submission)
            print("OK")
            print(flag)
            return 0
    except (OSError, ValueError, KeyError, TypeError, zlib.error) as error:
        print(f"NG: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
