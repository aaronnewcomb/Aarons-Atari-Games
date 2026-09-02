#!/usr/bin/env python3
"""Generate stage 4 data: accepted stage 3 plus the white M."""

from pathlib import Path

from generate_title_stage1_data import emit_table, pack, pf0, read_grid
from generate_title_stage3_data import stage3_grid


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "src" / "title_stage4_direct_data.inc"


def stage4_grid(source: list[str]) -> list[str]:
    rows = stage3_grid(source)
    result = []
    for y, stage3_row in enumerate(rows):
        row = list(stage3_row)
        if 14 <= y <= 22:
            # Add only M. E and its coral bars remain off for stage 5.
            for x in range(20, 27):
                if source[y][x] == "#":
                    row[x] = "#"
        result.append("".join(row))
    return result


def main() -> int:
    rows = stage4_grid(read_grid())
    tables = {
        "CineTitlePF0L": [pf0(row, 0) for row in rows],
        "CineTitlePF1L": [pack(row, 4) for row in rows],
        "CineTitlePF2L": [pack(row, 12, reverse=True) for row in rows],
        "CineTitlePF0R": [pf0(row, 20) for row in rows],
        "CineTitlePF1R": [pack(row, 24) for row in rows],
        "CineTitlePF2R": [pack(row, 32, reverse=True) for row in rows],
    }
    colors = [0x4A] * 66
    for y in (*range(5, 12), *range(14, 23)):
        colors[y] = 0x0E
    tables["CineTitlePFColors"] = colors
    tables["CineTitlePlayer"] = [0] * 66

    lines = [
        "; Generated stage 4 data: accepted stage 3 plus white M.",
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
