"""Standard-library verifier. The finale requires all three correct keys."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import sys


PARTS = {
    "echo": "8a0df808849c570c55c091c8ba5f8e54982a25a98e24805e66f70a80eab62b16",
    "chamber": "3376583242d4f917506c112470f733d44340633269c4358eadad81137aae94ca",
    "canon": "0fcb5f5ab6e535342876b287abaa77713ffbf3cf37ca161cd05b11db9c9e411c",
}
FINAL = "f0306e9e24bf617e841e129eaefa19f2a8a5a6a0e63c76dfa0b08a34797b3665"


def check_flag(flag, expected):
    if not isinstance(flag, str) or len(flag) > 256:
        raise ValueError("A flag must be a string of at most 256 characters")
    actual = hashlib.sha256(flag.encode("ascii")).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise ValueError("Flag mismatch")


def key_from_flags(flags):
    if not isinstance(flags, list) or len(flags) != 3:
        raise ValueError("Keys must be a three-element JSON array in echo, chamber, canon order")
    for name, flag in zip(PARTS, flags):
        try:
            check_flag(flag, PARTS[name])
        except ValueError as error:
            raise ValueError(f"{name}: {error}") from error
    return hashlib.sha256(
        b"silent-orchestra/keys/v1\0" + b"\0".join(flag.encode("ascii") for flag in flags)
    ).digest()


def xor_stream(data, key):
    result = bytearray()
    for offset in range(0, len(data), 32):
        block = hashlib.sha256(
            b"silent-orchestra/stream/v1\0" + key + (offset // 32).to_bytes(8, "big")
        ).digest()
        result.extend(a ^ b for a, b in zip(data[offset:offset + 32], block))
    return bytes(result)


def unlock(flags, seal):
    key = key_from_flags(flags)
    if not isinstance(seal, dict) or set(seal) != {"ciphertext", "tag"}:
        raise ValueError("Invalid score seal format")
    chunks, tag = seal["ciphertext"], seal["tag"]
    if not isinstance(chunks, list) or not all(isinstance(s, str) for s in chunks) or not isinstance(tag, str):
        raise ValueError("Invalid score seal format")
    if len(tag) != 64 or any(c not in "0123456789abcdef" for c in tag):
        raise ValueError("Invalid score seal format")
    ciphertext = bytes.fromhex("".join(chunks))
    actual = hmac.new(key, b"silent-orchestra/seal/v1\0" + ciphertext, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual, tag):
        raise ValueError("Score seal authentication failed")
    return json.loads(xor_stream(ciphertext, key).decode("utf-8"))


def check_final(flags, seal, flag):
    unlock(flags, seal)
    check_flag(flag, FINAL)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("sub", help="Check a sub-flag")
    sub.add_argument("part", choices=PARTS)
    sub.add_argument("flag")
    opening = commands.add_parser("open", help="Open the finale with all three keys")
    opening.add_argument("keys", type=Path)
    final = commands.add_parser("final", help="Check all three keys and the final flag")
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
            check_final(flags, seal, args.flag)
    except (OSError, ValueError) as error:
        print(f"NG: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
