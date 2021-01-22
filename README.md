# RuneKit

[![No Maintenance Intended](https://unmaintained.tech/badge.svg)](https://unmaintained.tech/)

Alt1-compatible toolbox for RuneScape 3, for Linux and macOS.

**Alpha quality software**

## What works

**Overlay are not supported yet**

App                            | Linux | macOS
-------------------------------|-------|----------
Clue solver (Text/Emote)       | ✅    | ✅
Clue solver (Map scroll)       | ?     | ?
Clue solver (Compass)          | ?     | 2
Clue solver (Scan)             | ?     | ?
Clue solver (Lockbox)          | ?     | ?
Clue solver (Celtic Knot)      | ?     | ✅
Clue solver (Slide)            | ?     | ✅
Clue solver (Towers)           | ?     | ?
Example app                    | ✅    | ✅
AfkWarden (Inactive)           | ❌    | ✅
AfkWarden (XP Counter)         | ❌    | ❌
AfkWarden (Chatbox)            | 1     | ✅
AfkWarden (Crafting menu)      | ✅    | ✅
AfkWarden (Buffs)              | ✅    | ✅
AfkWarden (Action bar stats)   | ✅    | ✅
AfkWarden (Dialog box)         | ✅    | ✅
AfkWarden (Target death)       | ?     | ?
AfkWarden (Sheathe stance)     | ?     | ?
AfkWarden (Castle Wars)        | ?     | ?
AfkWarden (Fight kiln waves)   | ?     | ?
AfkWarden (Target death)       | ?     | ?
AfkWarden (Item drops)         | ?     | ?

- 1: Can be setup but only fire once (needs inactive to work)
- 2: Detected but cannot place mark

## Running

This project use [Poetry](https://python-poetry.org) as package manager.

Requires Poetry 1.1

```sh
poetry install
poetry build
cp build/lib.*/runekit/image/*.cpython*.* runekit/image/
poetry run python main.py https://runeapps.org/apps/alt1/afkscape/appconfig.json
```

WIP Instruction:

- Run RuneScape before starting!!
- Linux: Game window MUST be ENTIRELY visible. (No minimize, no other window on top, including RuneKit)
- macOS: HiDPI (Retina) support may or may not work. Use external monitor for best result
- macOS: You will need to add Python in System Preferences > Security > Privacy in these sections:
  - Accessibility
  - Screen Recording: 
  - Note that it wmight appear as the closest macOS application (eg. your terminal emulator) instead of Python

## Developer

Start with `--remote-debugging-port=9222` to enable remote debugger protocol.
To debug, go to `chrome://inspect` on Chrome/Chromium.

## License

This protect is [No Maintenance Intended](https://unmaintained.tech/).
It is provided as-is and may not be actively maintained. There's no support, and no promise that pull requests will be
reviewed and merged. In other word: I wrote this for my own use and there's no point in keeping it to myself. However,
making it a proper open source project is an ongoing work.

This project is [licensed](LICENSE) under GPLv3, and contains code from [third parties](THIRD_PARTY_LICENSE.md).
Contains code from the Alt1 application.

Please do not contact Alt1 or RuneApps.org for support.
