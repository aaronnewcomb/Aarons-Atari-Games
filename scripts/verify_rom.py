#!/usr/bin/env python3
"""Perform structural checks on 4 KiB and 8 KiB Atari 2600 ROMs."""

from pathlib import Path
import sys


VALID_SIZES = {4096: "4K", 8192: "F8"}
ROM_BASE = 0xF000


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_rom.py ROM", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    data = path.read_bytes()

    if len(data) not in VALID_SIZES:
        print(
            f"error: {path} is {len(data)} bytes, expected 4096 or 8192",
            file=sys.stderr,
        )
        return 1

    banks = [data] if len(data) == 4096 else [data[:4096], data[4096:]]
    vectors = []
    for bank_number, bank in enumerate(banks):
        nmi = int.from_bytes(bank[-6:-4], "little")
        reset = int.from_bytes(bank[-4:-2], "little")
        irq = int.from_bytes(bank[-2:], "little")
        for name, vector in (("NMI", nmi), ("RESET", reset), ("IRQ", irq)):
            if not ROM_BASE <= vector <= 0xFFFF:
                print(
                    f"error: bank {bank_number} {name} vector ${vector:04X} "
                    "is outside cartridge ROM",
                    file=sys.stderr,
                )
                return 1
        vectors.append((nmi, reset, irq))

    vector_text = "; ".join(
        f"bank {index}: NMI=${nmi:04X}, RESET=${reset:04X}, IRQ=${irq:04X}"
        for index, (nmi, reset, irq) in enumerate(vectors)
    )
    print(f"verified {path}: {len(data)} bytes ({VALID_SIZES[len(data)]}); {vector_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
