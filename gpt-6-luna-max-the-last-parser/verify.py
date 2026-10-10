"""Validate subflags, the sealed finale, and the final flag using only the standard library."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import sys


PARTS = {
    "precedence": "7cb02a95a54ad89b28537dce1bbe18f2083ca0071467632508076eebce90630a",
    "associativity": "100156fdbcb5fec80f9e1835a100a664ca1b07bfa9ded5e24c1418597abcbca4",
    "composition": "2992e30748e20bf17b25fee10b2e32cbc1032806d7bda72073400aff3c1c30f6",
}
FINAL = "da4db66d542f962857ff992cb621250ab2e8215116efe5256b02eace02d8b1cc"


def check_flag(flag, expected):
    if not isinstance(flag, str) or len(flag) > 256:
        raise ValueError("flag must be a string no longer than 256 characters")
    actual = hashlib.sha256(flag.encode("ascii")).hexdigest()
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
        b"last-parser/keys/v1\0" + b"\0".join(flag.encode("ascii") for flag in flags)
    ).digest()


def xor_stream(data, key):
    result = bytearray()
    for offset in range(0, len(data), 32):
        block = hashlib.sha256(
            b"last-parser/stream/v1\0" + key + (offset // 32).to_bytes(8, "big")
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
    actual = hmac.new(key, b"last-parser/seal/v1\0" + ciphertext, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual, tag):
        raise ValueError("seal is corrupted")
    return json.loads(xor_stream(ciphertext, key).decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("sub", help="validate a subflag")
    sub.add_argument("part", choices=PARTS)
    sub.add_argument("flag")
    opening = commands.add_parser("open", help="open the final expression with all three subflags")
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
            seal = json.loads(Path(__file__).with_name("finale.seal.json").read_text(encoding="utf-8"))
            if args.command == "open":
                print(json.dumps(unlock(flags, seal), ensure_ascii=False, indent=2))
                return 0
            unlock(flags, seal)
            check_flag(args.flag, FINAL)
    except (OSError, ValueError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
