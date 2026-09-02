#!/usr/bin/env python3
"""Generate the clean-room stage 1 playfield tables from the native grid."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "resources" / "title_playfield.txt"
OUTPUT = ROOT / "src" / "title_stage1_direct_data.inc"


def read_grid() -> list[str]:
    rows = [line.strip() for line in SOURCE.read_text().splitlines() if line.strip()]
    if len(rows) != 66 or any(len(row) != 40 for row in rows):
        raise ValueError("title_playfield.txt must contain 66 rows of 40 cells")
    return rows


def stage1_grid(rows: list[str]) -> list[str]:
    result = []
    for y, row in enumerate(rows):
        keep = {0, 39}
        if y == 0 or y == 65:
            keep.update(range(40))
        elif y in {5, 11}:
            # White top and bottom caps of the first O. The five middle rows
            # are emitted by the fixed-cycle COLUPF kernel, not by P0/P1.
            keep.update(range(8, 11))
        elif 6 <= y <= 10:
            # Solid O body. COLUPF changes white -> coral -> white while the
            # beam crosses this span, leaving white rails around its middle.
            keep.update(range(7, 12))
        result.append("".join("#" if x in keep else "." for x in range(40)))
    return result


def pf0(row: str, start: int) -> int:
    return sum((1 << (4 + i)) for i in range(4) if row[start + i] == "#")


def pack(row: str, start: int, reverse: bool = False) -> int:
    value = 0
    for i in range(8):
        if row[start + i] == "#":
            value |= 1 << (i if reverse else 7 - i)
    return value


def emit_table(lines: list[str], label: str, values: list[int]) -> None:
    lines.append(f"{label}:")
    for start in range(0, len(values), 8):
        lines.append("        byte " + ",".join(f"${v:02X}" for v in values[start:start + 8]))
    lines.append("")


def main() -> int:
    rows = stage1_grid(read_grid())
    tables = {
        "CineTitlePF0L": [pf0(row, 0) for row in rows],
        "CineTitlePF1L": [pack(row, 4) for row in rows],
        # PF2 is drawn least-significant bit first on both halves.
        "CineTitlePF2L": [pack(row, 12, reverse=True) for row in rows],
        "CineTitlePF0R": [pf0(row, 20) for row in rows],
        "CineTitlePF1R": [pack(row, 24) for row in rows],
        "CineTitlePF2R": [pack(row, 32, reverse=True) for row in rows],
    }
    colors = [0x4A] * 66
    for y in range(5, 12):
        colors[y] = 0x0E
    tables["CineTitlePFColors"] = colors
    tables["CineTitlePlayer"] = [0] * 66

    lines = [
        "; Generated from resources/title_playfield.txt for clean-room stage 1.",
        "; Only the frame and first O are present in this source grid.",
        "",
        "        align 256",
    ]
    for label, values in tables.items():
        if label in {"CineTitlePF0R", "CineTitlePFColors"}:
            lines.append("        align 256")
        emit_table(lines, label, values)
    OUTPUT.write_text("\n".join(lines).rstrip() + "\n")
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
