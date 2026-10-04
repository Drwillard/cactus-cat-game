# Cactus Cat

A desert runner for ModRetro Chromatic, Game Boy Color, and the original monochrome Game Boy. Choose an orange, black, white, or blue cat—or a brown dog—and see how far you can travel through a desert with slowly scrolling mountains and original synthpop music.

## Gameplay

Jump over three varieties of cacti, rivers, and holes. Duck under low-flying birds and stay grounded beneath high-flying birds. Hitting a hazard or falling into a river or hole ends the run.

Each obstacle cleared earns **1 point**. Eat blue fish for **5 bonus points**: they appear at randomized heights and distances, so some require a jump. Missing a fish has no penalty.

The game speeds up after every ten obstacles cleared, up to a maximum speed. Fish bonuses do not increase the speed. Your best score lasts until power-off, and your chosen pet stays selected when you retry.

## Controls

- **Left / Right:** choose your pet before play.
- **A / Start:** confirm your pet or retry after game over.
- **A / Up:** tap for a short hop or hold for a full jump. Releasing early cuts the ascent; pressing again in midair does not restore it.
- **Down / B:** hold to duck under low birds.
- **Start:** pause or resume during a run.
- **Select:** toggle the synthpop music.
- **B after game over:** return to the pet picker.

Hold jump to clear tall cacti and wider gaps. Scenery and hazards stop while paused.

## Load on Chromatic

The compiled ROM is `build/cactus-cat.gbc`. Use a compatible writable Game Boy / Game Boy Color cartridge, or the DevDay Edition developer cartridge.

With developer mode activated, use the Chromatic Firmware Updater’s **HOMEBREW** button to select the ROM. Wait for the write to finish successfully, then restart the console. Flashing replaces the game on the selected cartridge.

[ModRetro DevDay setup guide](https://support.modretro.com/en_us/chromatic-devday-edition-quickstart-guid-By1iOlcMg)

## Build

Download [GBDK 2020 4.5.0](https://github.com/gbdk-2020/gbdk-2020/releases) for your platform and unpack it as `tools/gbdk`, then run `make`. Alternatively, run `make GBDK=/path/to/gbdk`.

Game logic is in `src/main.c`, music is in `src/music.h`, and editable pixel-art patterns are in `tools/make_art.py`. No commercial ROMs or assets are included.

## Emulator checks

With `pyboy` and `pillow` installed, run:

```sh
python tools/test_rom.py
python tools/test_jump.py
```

The checks exercise character selection, hazards, fish scoring, scrolling scenery, pause, restart, music, and variable-height jumps through actual ROM button input. Screenshots are saved in `build/`.
