#!/usr/bin/env python3
"""Generate stage 2 data: verified coral O, white CTO, and white G."""

from pathlib import Path

from generate_title_stage1_data import emit_table, pack, pf0, read_grid


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "src" / "title_stage2_direct_data.inc"


def stage2_grid(source: list[str]) -> list[str]:
    result = []
    for y in range(66):
        keep = {0, 39}
        if y == 0 or y == 65:
            keep.update(range(40))
        elif 5 <= y <= 11:
            # Preserve the verified first-O geometry. Add C, T, and the
            # second O from the calibrated source, shifted up one logical row
            # so all four letters share the accepted first-O baseline.
            if y in {5, 11}:
                keep.update(range(8, 11))
            else:
                keep.update(range(7, 12))
            source_y = y + 1
            keep.update(
                x for x in range(13, 36) if source[source_y][x] == "#"
            )
        elif 14 <= y <= 22:
            # Stage 2 adds only G on the second line. A, M, and E remain off.
            keep.update(x for x in range(6, 13) if source[y][x] == "#")
        result.append("".join("#" if x in keep else "." for x in range(40)))
    return result


def main() -> int:
    rows = stage2_grid(read_grid())
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
    for y in (*range(5, 12), *range(14, 23)):
        colors[y] = 0x0E
    tables["CineTitlePFColors"] = colors
    tables["CineTitlePlayer"] = [0] * 66

    lines = [
        "; Generated stage 2 data: coral O, white CTO, and white G only.",
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
