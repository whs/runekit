# RuneKit

Alt1-compatible toolbox for RuneScape 3, for Linux.

**In development**

## What works

- Clue solver (not tested: sliding puzzle)
- Example app
- AfkWarden
  - [ ] Inactive
  - [ ] XP Counter
  - [x] Chatbox
  - [x] Crafting menu
  - [x] Buffs
  - [x] Action bar stats
  - [x] Dialog box
  - [x] Target death
  - I don't use these, please test: Sheathe stance, Castle Wars, Fight kiln waves, Target death, Item drops

## Running

This project use [Poetry](https://python-poetry.org) as package manager.

Requires Qt5 to be installed and Poetry 1.1

```sh
poetry install
poetry build
cp build/lib.*/runekit/image/*.cpython*.* runekit/image/
poetry run python main.py https://runeapps.org/apps/alt1/afkscape/appconfig.json
```

WIP Instruction:

- Run RuneScape before starting!!
- Game window MUST be ENTIRELY visible. (No minimize, no other window on top, including RuneKit)
