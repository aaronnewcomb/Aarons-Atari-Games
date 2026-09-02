#!/usr/bin/env python3
"""Generate stage 5 data: accepted stage 4 plus the E geometry."""

from pathlib import Path

from generate_title_stage1_data import emit_table, pack, pf0, read_grid
from generate_title_stage4_data import stage4_grid


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "src" / "title_stage5_direct_data.inc"


def stage5_grid(source: list[str]) -> list[str]:
    rows = stage4_grid(source)
    result = []
    for y, stage4_row in enumerate(rows):
        row = list(stage4_row)
        if 14 <= y <= 22:
            # Add only E. Its coral stripe rows are colored by the fixed-cycle
            # stage-5 kernel; the playfield table supplies the complete shape.
            for x in range(28, 33):
                if source[y][x] == "#":
                    row[x] = "#"
        result.append("".join(row))
    return result


def main() -> int:
    rows = stage5_grid(read_grid())
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
        "; Generated stage 5 data: accepted stage 4 plus E geometry.",
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
