#!/usr/bin/env python3
"""Build stage 6: complete title scene below the accepted stage-5 text."""

from pathlib import Path
import hashlib
import subprocess


ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
ROM = BUILD / "octo-game-title-stage6-8k.a26"
DASM = ROOT / "resources" / "tools" / "dasm-2.20.17" / "dasm"


def assemble(source: str, output: Path, *defines: str) -> None:
    command = [
        str(DASM),
        source,
        "-f3",
        "-v0",
        "-Iresources/includes",
        *[f"-D{define}" for define in defines],
        f"-o{output}",
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    BUILD.mkdir(exist_ok=True)
    subprocess.run(["python3", "scripts/generate_title_stage6_data.py"], cwd=ROOT, check=True)
    bank0 = BUILD / "title-stage6-bank0.bin"
    bank1 = BUILD / "title-stage6-bank1.bin"
    assemble(
        "src/title_stage1_bank0.asm",
        bank0,
        "TITLE_STAGE2=1",
        "TITLE_STAGE3=1",
        "TITLE_STAGE4=1",
        "TITLE_STAGE5=1",
        "TITLE_STAGE6=1",
    )
    # Stage 6 draws all 66 scene rows, then returns at the original footer
    # entry. Do not enable the reduced-stage blank remainder or silent title.
    assemble("src/main.asm", bank1, "F8_TITLE_O_EXPERIMENT=1")

    bank0_data = bank0.read_bytes()
    bank1_data = bank1.read_bytes()
    if len(bank0_data) != 4096 or len(bank1_data) != 4096:
        raise SystemExit("error: F8 banks must each be exactly 4096 bytes")
    ROM.write_bytes(bank0_data + bank1_data)
    digest = hashlib.sha256(ROM.read_bytes()).hexdigest()
    print(f"built {ROM}: {ROM.stat().st_size} bytes, sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
