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

This project uses [Poetry](https://python-poetry.org) as package manager.
Ensure that your `poetry --version` is 1.1.14 or higher.

Requires Qt5 to be installed

```sh
poetry install --no-dev
poetry build
cp build/lib.*/runekit/image/*.cpython*.* runekit/image/
python main.py https://runeapps.org/apps/alt1/afkscape/appconfig.json
```
If the last line above has issues please try using this:
```poetry run python main.py https://runeapps.org/apps/alt1/afkscape/appconfig.json```

All required packages should be automatically installed, however some reported requiring to `pip3 install` the below packages:
```click
qtutils
pymitter
Xlib```

WIP Instructions:

- Run RuneScape before starting!!
- Game window MUST be ENTIRELY visible. (No minimize, no other window on top, including RuneKit)
