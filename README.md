# RuneKit

Alt1-compatible toolbox for RuneScape 3, for Linux.

**In development**

## What works

- Clue solver
- Example app

## Running

This project use [Poetry](https://python-poetry.org) as package manager.

Requires Qt5 to be installed

```sh
poetry install --no-dev
poetry build
cp build/lib.*/runekit/image/*.cpython*.* runekit/image/
python main.py https://runeapps.org/apps/alt1/afkscape/appconfig.json
```

WIP Instruction:

- Run RuneScape before starting!!
- Game window MUST be ENTIRELY visible. (No minimize, no other window on top, including RuneKit)
