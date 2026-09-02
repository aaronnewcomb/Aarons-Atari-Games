# Octo Game

**Octo Game** is an original Atari 2600 game inspired by the classic
Red Light, Green Light playground challenge. Guide your octopus across the
arena while the light is green, freeze when it turns red, and survive all nine
levels.

The game is a homebrew 8 KiB NTSC cartridge written in 6502 assembly. It
features a custom title screen, original TIA music and sound effects, randomized
light timing, obstacle courses, scoring, and a final victory screen.

## Download and play

The latest tested cartridge image is available from the
[Octo Game v0.3.0 release](https://github.com/aaronnewcomb/Aarons-Atari-Games/releases/tag/v0.3.0).

[Read the graphical manual](docs/manual.md) or
[download the PDF edition](https://github.com/aaronnewcomb/Aarons-Atari-Games/releases/download/v0.3.0/octo-game-v0.3.0-manual.pdf).

Download `octo-game.a26`, then open it with an Atari 2600 emulator such as
[Stella](https://stella-emu.github.io/). The ROM can also be used with
compatible flash cartridges and original hardware configured for an 8 KiB F8
cartridge.

## How to play

1. Press **Fire** on the title screen.
2. Move **Up** while the light is green to advance toward the finish line.
3. Use **Left** and **Right** to steer around obstacles.
4. Release the joystick completely when the light turns red.
5. Reach the finish line before the timer reaches `000`.
6. Complete all nine levels to survive.

Any joystick direction during a red light causes immediate elimination. The
green and red phases use randomized timing, and the intervals become shorter
as the levels advance.

### Controls

| Input | Action |
| --- | --- |
| Fire on title screen | Start a new game |
| Joystick Up | Move toward the finish line during a green light |
| Joystick Left or Right | Steer during a green light |
| Fire after elimination | Restart at level 1 |
| Fire on victory screen | Play again |
| Console Reset | Return to the title screen |

Stella normally maps the joystick to the arrow keys and Fire to Space or Left
Control. RetroArch's Stella core commonly maps Fire to Z. Emulator settings
may use different bindings.

## Levels, obstacles, and scoring

- The game contains nine progressively faster levels.
- Levels 2, 4, 6, and 8 contain one tree and two boulders.
- Obstacle positions are randomized at the beginning of each round.
- Obstacles have solid collision, so the octopus must move around them.
- Each round begins with a timer of `999`, which reaches `000` after 30 seconds.
- Completing a level awards 100 points plus the remaining timer value.
- The four-digit score display stops at `9999`.
- Completing level 9 opens the final survival screen and displays the score.

## Features

- Custom `OCTO GAME` title artwork with coral inlays
- Animated teal octopus mascot and blue pedestal
- Original title music played through the Atari TIA
- Distinct light-change, elimination, and level-clear sounds
- Randomized red and green light durations
- Nine-level difficulty progression
- Randomized obstacle courses on alternating levels
- Three-digit countdown timer and four-digit cumulative score
- Dedicated victory screen after level 9
- Stable 262-scanline NTSC display
- 8 KiB F8 bank switching with 128 bytes of Atari 2600 RAM

## Building from source

### Requirements

- Python 3
- GNU Make
- [DASM](https://github.com/dasm-assembler/dasm), version 2.20.x recommended
- Stella, optional, for running and inspecting the ROM

Build and verify the release ROM:

```sh
make
```

The finished cartridge is written to:

```text
build/octo-game.a26
```

The build generates the title data, assembles both 4 KiB F8 banks, combines
them into the final 8 KiB ROM, and verifies the interrupt vectors in each bank.
The Makefile uses the local DASM executable under `resources/tools/` when it is
available, otherwise it uses `dasm` from `PATH`.

Additional commands:

```sh
make verify       # Verify the current cartridge structure and vectors
make rominfo      # Inspect the cartridge with Stella
make run          # Build and launch the game in Stella
make legacy-4k    # Build the preserved pre-title 4 KiB checkpoint
make clean        # Remove generated files from build/
```

## Cartridge information

| Property | Value |
| --- | --- |
| Platform | Atari 2600 / Video Computer System |
| Television standard | NTSC |
| ROM size | 8,192 bytes |
| Bankswitching | F8, two 4 KiB banks |
| RAM | 128 bytes |
| Language | MOS 6502 assembly |
| Assembler | DASM |
| Current release | v0.3.0 |
| Release SHA-256 | `991d1242458e72724fa418dc7d008bbf1be916fe034c66a2a06e5a4e4657cdd4` |

## Source layout

```text
src/main.asm                        Gameplay, sound, footer, and game states
src/title_stage1_bank0.asm          Dedicated bank-0 title kernel
src/title_stage*_direct_data.inc    Generated staged title data
scripts/generate_title_stage*_data.py
                                    Title playfield generators
scripts/build_title_stage*_8k.py    Staged and release ROM builders
scripts/verify_rom.py               4 KiB and 8 KiB structural verification
resources/title_playfield.txt       Native 40-column title artwork source
resources/includes/                 Atari register definitions and macros
build/                              Generated cartridges and diagnostics
```

The title screen was developed in six verified stages. Each stage preserved the
previous title pixels while adding the next letters, coral color transitions,
mascot, pedestal, footer, and finally the music. The final release target is
`title-stage6-music-8k`.

## Project status

Version 0.3.0 is the current tested one-player release. A future version may use
the reserved `GameMode` state for a two-player mode selected with the console
Select switch.

## Credits

Designed and programmed by Aaron Newcomb, 2026.

## License

This project is distributed under the GNU General Public License v3.0. See the
repository [LICENSE](../../LICENSE) for the complete terms.
