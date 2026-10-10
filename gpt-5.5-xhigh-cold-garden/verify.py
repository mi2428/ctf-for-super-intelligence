"""Validate subflags, the sealed finale, and the final flag using only the standard library."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import sys


PARTS = {
    "stalk": "50a74d0b72c25b36f45d738c4f8766e6c7bd93f8c0392b053715efd2dabf9454",
    "grove": "b52540169856618bc072e6b2f2c08c7d89aaef8343cf46ba0be6858667ffee0e",
    "needle": "fef6afc6a46b5872538fb838152eee0617c59337d4582741c03cfc83599e7327",
}
FINAL = "cdcb9464601d256045df541e94240872cb25de1f42e20a747372d60ec804b623"


def ascii_bytes(flag):
    if not isinstance(flag, str) or len(flag) > 256:
        raise ValueError("flag must be a string no longer than 256 characters")
    try:
        return flag.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("flag must be ASCII") from error


def check_flag(flag, expected):
    actual = hashlib.sha256(ascii_bytes(flag)).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise ValueError("flag does not match")


def key_from_flags(flags):
    if not isinstance(flags, list) or len(flags) != len(PARTS):
        raise ValueError("keys must be a JSON array of three subflags in the specified order")
    for name, flag in zip(PARTS, flags):
        try:
            check_flag(flag, PARTS[name])
        except ValueError as error:
            raise ValueError(f"{name}: {error}") from error
    return hashlib.sha256(
        b"cold-garden/keys/v1\0" + b"\0".join(ascii_bytes(flag) for flag in flags)
    ).digest()


def xor_stream(data, key):
    result = bytearray()
    for offset in range(0, len(data), 32):
        block = hashlib.sha256(
            b"cold-garden/stream/v1\0" + key + (offset // 32).to_bytes(8, "big")
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
    actual = hmac.new(key, b"cold-garden/seal/v1\0" + ciphertext, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual, tag):
        raise ValueError("seal is corrupted")
    return json.loads(xor_stream(ciphertext, key).decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("sub", help="validate a subflag")
    sub.add_argument("part", choices=PARTS)
    sub.add_argument("flag")
    opening = commands.add_parser("open", help="open the final grove with all three subflags")
    opening.add_argument("keys", type=Path)
    final = commands.add_parser("final", help="validate the final flag and all three subflags")
    final.add_argument("keys", type=Path)
    final.add_argument("flag")
    args = parser.parse_args()
    try:
        if args.command == "sub":
            check_flag(args.flag, PARTS[args.part])
        else:
            flags = json.loads(args.keys.read_text(encoding="utf-8"))
            seal = json.loads(Path(__file__).with_name("final.seal.json").read_text(encoding="utf-8"))
            if args.command == "open":
                print(json.dumps(unlock(flags, seal), ensure_ascii=False, indent=2))
                return 0
            unlock(flags, seal)
            check_flag(args.flag, FINAL)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
