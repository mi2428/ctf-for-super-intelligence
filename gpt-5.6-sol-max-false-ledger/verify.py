"""Verify the three sub-flags and unlock the final audit."""

import argparse
import hashlib
import hmac
import json
from pathlib import Path
import sys


PARTS = {
    "repair": "4d07f8dac318ef936fc559088d5d7f1f2b08d04f404f2d6809b257704a9d7a23",
    "lineage": "8780a14cc2fdb5ab84b9d405fd52f689f33e685bc0142c37b7c503bcbc23117a",
    "reassure": "444a3ea4bc5c611ed084130ada0a729d4d920a6d6b2ccc8be35728c724814923",
}
FINAL = "837c010d388df0a024d9917c990a2b7cbb8b905e1b3ba1fb3c6e5e39ce285d96"


def check_flag(flag, expected):
    if not isinstance(flag, str) or len(flag) > 256:
        raise ValueError("A flag must be a string of at most 256 characters")
    try:
        actual = hashlib.sha256(flag.encode("ascii")).hexdigest()
    except UnicodeEncodeError as error:
        raise ValueError("A flag must contain ASCII characters only") from error
    if not hmac.compare_digest(actual, expected):
        raise ValueError("Flag mismatch")


def key_from_flags(flags):
    if not isinstance(flags, list) or len(flags) != 3:
        raise ValueError("Keys must be a three-element JSON array in repair, lineage, reassure order")
    for name, flag in zip(PARTS, flags):
        try:
            check_flag(flag, PARTS[name])
        except ValueError as error:
            raise ValueError(f"{name}: {error}") from error
    return hashlib.sha256(
        b"false-ledger/keys/v1\0" + b"\0".join(flag.encode("ascii") for flag in flags)
    ).digest()


def xor_stream(data, key):
    result = bytearray()
    for offset in range(0, len(data), 32):
        block = hashlib.sha256(
            b"false-ledger/stream/v1\0" + key + (offset // 32).to_bytes(8, "big")
        ).digest()
        result.extend(a ^ b for a, b in zip(data[offset:offset + 32], block))
    return bytes(result)


def unlock(flags, seal):
    key = key_from_flags(flags)
    if not isinstance(seal, dict) or set(seal) != {"ciphertext", "tag"}:
        raise ValueError("Invalid seal format")
    ciphertext_hex, tag = seal["ciphertext"], seal["tag"]
    lower_hex = set("0123456789abcdef")
    if (
        not isinstance(ciphertext_hex, str)
        or not ciphertext_hex
        or len(ciphertext_hex) % 2
        or any(character not in lower_hex for character in ciphertext_hex)
        or not isinstance(tag, str)
        or len(tag) != 64
        or any(character not in lower_hex for character in tag)
    ):
        raise ValueError("Invalid seal format")
    ciphertext = bytes.fromhex(ciphertext_hex)
    actual = hmac.new(
        key, b"false-ledger/seal/v1\0" + ciphertext, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(actual, tag):
        raise ValueError("Seal authentication failed")
    task = json.loads(xor_stream(ciphertext, key).decode("ascii"))
    if not isinstance(task, dict):
        raise ValueError("Invalid final task")
    return task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("sub", help="Check one sub-flag")
    sub.add_argument("part", choices=PARTS)
    sub.add_argument("flag")
    opening = commands.add_parser("open", help="Open the final audit with all three keys")
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
            seal = json.loads(Path(__file__).with_name("final.seal.json").read_text(encoding="utf-8"))
            task = unlock(flags, seal)
            if args.command == "open":
                print(json.dumps(task, ensure_ascii=False, indent=2))
                return 0
            check_flag(args.flag, FINAL)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"NG: {error}", file=sys.stderr)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
