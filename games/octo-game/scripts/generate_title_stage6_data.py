#!/usr/bin/env python3
"""Generate the complete title scene below the accepted stage-5 lettering."""

from pathlib import Path

from generate_title_stage1_data import emit_table, pack, pf0, read_grid
from generate_title_stage5_data import stage5_grid


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "src" / "title_stage6_direct_data.inc"


def stage6_grid(source: list[str]) -> list[str]:
    """Preserve stage 5 through row 22, then restore the lower scene."""
    accepted = stage5_grid(source)
    return [accepted[y] if y <= 22 else source[y] for y in range(66)]


def main() -> int:
    source = read_grid()
    rows = stage6_grid(source)
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
    for y, color in enumerate(range(0x82, 0x90, 2), start=56):
        colors[y] = color
    # The source contains two equally wide lowest pedestal rows. Keep both
    # blue, as shown in the reference, before the coral frame resumes.
    colors[63] = 0x8E
    tables["CineTitlePFColors"] = colors

    player = [0] * 66
    player[43:55] = [
        0x3C,
        0x7E,
        0xFF,
        0xDB,
        0xFF,
        0x7E,
        0x3C,
        0x7E,
        0xDB,
        0x99,
        0x5A,
        0xA5,
    ]
    tables["CineTitlePlayer"] = player

    lines = [
        "; Generated stage 6 data: accepted stage 5 plus lower title scene.",
        "; Rows 0-22 remain byte-for-byte compatible with stage 5.",
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
