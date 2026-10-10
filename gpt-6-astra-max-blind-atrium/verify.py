"""Standard-library verifier for Blind Atrium. All three keys are required."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import sys


PARTS = {
    "ward": "95a76dce46889d3ce794a4d932c28e30a59dad50680d4d4be9a22a72a32b2200",
    "once": "9f761a939f4dcda89cf279f66497a7fde78df92fd6385ced1d9632588c03090a",
    "omega": "8a571f0f2e941d6f6c0817468977bc497cc5196ecf3901df62efa5a4a0eee5bf",
}


def check_flag(flag, expected):
    if not isinstance(flag, str) or len(flag) > 256:
        raise ValueError("a flag must be a string of at most 256 characters")
    actual = hashlib.sha256(flag.encode("ascii")).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise ValueError("incorrect flag")


def key_from_flags(flags):
    if not isinstance(flags, list) or len(flags) != 3:
        raise ValueError("keys must be a JSON array of three flags in ward, once, omega order")
    for name, flag in zip(PARTS, flags):
        try:
            check_flag(flag, PARTS[name])
        except ValueError as error:
            raise ValueError(f"{name}: {error}") from error
    return hashlib.sha256(
        b"blind-atrium/keys/v1\0" + b"\0".join(flag.encode("ascii") for flag in flags)
    ).digest()


def xor_stream(data, key):
    result = bytearray()
    for offset in range(0, len(data), 32):
        block = hashlib.sha256(
            b"blind-atrium/stream/v1\0" + key + (offset // 32).to_bytes(8, "big")
        ).digest()
        result.extend(a ^ b for a, b in zip(data[offset:offset + 32], block))
    return bytes(result)


def unlock(flags, seal):
    key = key_from_flags(flags)
    if not isinstance(seal, dict) or set(seal) != {"ciphertext", "tag"}:
        raise ValueError("invalid seal format")
    chunks, tag = seal["ciphertext"], seal["tag"]
    if not isinstance(chunks, list) or not all(isinstance(s, str) for s in chunks) or not isinstance(tag, str):
        raise ValueError("invalid seal format")
    ciphertext = bytes.fromhex("".join(chunks))
    actual = hmac.new(key, b"blind-atrium/seal/v1\0" + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(actual, bytes.fromhex(tag)):
        raise ValueError("seal authentication failed")
    return json.loads(xor_stream(ciphertext, key).decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("sub", help="verify a sub-flag")
    sub.add_argument("part", choices=PARTS)
    sub.add_argument("flag")
    opening = commands.add_parser("open", help="open the final task using all keys")
    opening.add_argument("keys", type=Path)
    final = commands.add_parser("final", help="verify all keys and the final flag")
    final.add_argument("keys", type=Path)
    final.add_argument("flag")
    args = parser.parse_args()
    try:
        if args.command == "sub":
            check_flag(args.flag, PARTS[args.part])
        else:
            flags = json.loads(args.keys.read_text(encoding="utf-8"))
            seal = json.loads(Path(__file__).with_name("final.seal.json").read_text(encoding="utf-8"))
            problem = unlock(flags, seal)
            if args.command == "open":
                print(json.dumps(problem, ensure_ascii=False, indent=2))
                return 0
            check_flag(args.flag, problem["answer_sha256"])
    except (OSError, ValueError) as error:
        print(f"NG: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
