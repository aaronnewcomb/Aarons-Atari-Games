#!/usr/bin/env python3
"""Perform small structural checks on a 4 KiB Atari 2600 ROM."""

from pathlib import Path
import sys


EXPECTED_SIZE = 4096
ROM_BASE = 0xF000


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_rom.py ROM", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    data = path.read_bytes()

    if len(data) != EXPECTED_SIZE:
        print(
            f"error: {path} is {len(data)} bytes, expected {EXPECTED_SIZE}",
            file=sys.stderr,
        )
        return 1

    nmi = int.from_bytes(data[-6:-4], "little")
    reset = int.from_bytes(data[-4:-2], "little")
    irq = int.from_bytes(data[-2:], "little")

    for name, vector in (("NMI", nmi), ("RESET", reset), ("IRQ", irq)):
        if not ROM_BASE <= vector <= 0xFFFF:
            print(
                f"error: {name} vector ${vector:04X} is outside cartridge ROM",
                file=sys.stderr,
            )
            return 1

    print(
        f"verified {path}: {len(data)} bytes, "
        f"NMI=${nmi:04X}, RESET=${reset:04X}, IRQ=${irq:04X}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

