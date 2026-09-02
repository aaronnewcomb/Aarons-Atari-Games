# Aaron's Atari Games

Original homebrew games designed for the Atari 2600 Video Computer System.
Each game has its own source code, build instructions, README, graphical manual,
and downloadable cartridge release.

## Games

### Octo Game

Guide an octopus through nine increasingly difficult rounds of Red Light,
Green Light. Move while the light is green, freeze when it turns red, and steer
around trees and boulders on the obstacle levels.

- [Game information and build instructions](games/octo-game/README.md)
- [Graphical game manual](games/octo-game/docs/manual.md)
- [Download the v0.3.0 ROM](https://github.com/aaronnewcomb/Aarons-Atari-Games/releases/tag/v0.3.0)
- [Browse the source](games/octo-game/src/)

## Repository layout

```text
games/
└── octo-game/
    ├── README.md
    ├── Makefile
    ├── src/
    ├── scripts/
    ├── resources/
    ├── build/
    └── docs/
        ├── manual.md
        ├── manual.pdf
        └── manual-pages/
```

Additional games can be added as independent directories under `games/`.

## Building

Build a specific game from the repository root:

```sh
make octo-game
```

Or enter its directory and use its own Makefile:

```sh
cd games/octo-game
make
```

## License

Unless a game directory states otherwise, source code in this repository is
distributed under the GNU General Public License v3.0. See [LICENSE](LICENSE).
