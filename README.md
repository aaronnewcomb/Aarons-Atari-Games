# Octo Game

An original Atari 2600 interpretation of Red Light, Green Light. Move the
octopus toward the finish line while the doll is facing away. If the joystick
moves forward while the doll is watching, the octopus is eliminated and a
gunshot sound plays.

The target is an 8 KiB NTSC F8 bank-switched cartridge. The existing game and
footer remain in the gameplay bank, while the dedicated title kernel and
generated artwork live in the title bank.

## Quick start

Build the release ROM with DASM and Python 3:

```sh
make
```

The result is `build/octo-game.a26`, the verified 8 KiB F8 cartridge with the
complete title screen, title music, and gameplay. The build checks both banks
and their interrupt vectors.

Run it with an installed Stella emulator:

```sh
make run
```

The pinned Linux DASM binary is used when present. Otherwise the build uses a
`dasm` executable from `PATH`.

## Controls

- Fire on the intro screen: start a new game
- Joystick Up: move toward the finish line during a green light
- Joystick Left/Right: steer around obstacles during a green light
- Fire after elimination: restart from level one
- Fire on the victory screen: play again from level one
- Console Reset switch: return to the intro screen

Standalone Stella maps movement to the arrow keys and Fire to Space or Left
Control by default. With RetroArch's Stella core, the default keyboard Fire
binding is Z. Emulator input settings can change these mappings.

## Layout

```text
src/main.asm          game and display kernel
scripts/verify_rom.py structural 4 KiB/8 KiB ROM checks
resources/            pinned tools, includes, manuals, licenses, and links
build/                generated ROM, listing, and symbols
```

## Current prototype

- Cinematic `OCTO GAME` intro with a framed stage, large title lettering,
  pulsing octopus mascot, stepped pedestal, and a commercial-style 48-pixel
  fine-text kernel for the copyright, design credit, and Fire prompt
- Original single-channel TIA title music based on the supplied track's eerie
  drone and descending replies, lowered one octave and without the repeating
  drum pulse
- Stable NTSC frame structure
- Red and green light phases with randomized timing
- Immediate movement detection during red lights
- Distinct gunshot, light-change, and level-clear sounds
- Nine progressively faster levels
- Two gray boulders and one tree on levels 2, 4, 6, and 8, randomized at the
  start of each round and confined to the inner arena
- Solid obstacle collision, so the octopus must steer around each object
- A three-digit timer that falls from 999 to 000 in 30 seconds
- Level award of 100 points plus every point remaining on the timer
- Four-digit cumulative score that saturates at 9999
- A black victory screen after level 9 with green `YOU SURVIVED!`, red
  `for now ...`, a white `FINAL SCORE:` block, the five-digit value, and
  `PRESS FIRE TO PLAY AGAIN`
- Asymmetric HUD kernel with score on the left and timer on the right, neither
  mirrored
- Fixed 8 KiB ROM and 128-byte RAM constraints

The first milestone is intentionally one-player. `GameMode` is reserved in RAM
for the next pass, where the console Select switch will choose one-player or
two-player mode.
