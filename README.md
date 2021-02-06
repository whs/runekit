# RuneKit

[![No Maintenance Intended](https://unmaintained.tech/badge.svg)](https://unmaintained.tech/)

Alt1-compatible toolbox for RuneScape 3, for Linux and macOS.

## What works

| App                                                                             | Linux  | macOS  |
| ------------------------------------------------------------------------------- | ------ | ------ |
| **Clue Solver**                                                                 | &nbsp; | &nbsp; |
| - Text/Emote                                                                    | ✅     | ✅     |
| - Map scroll                                                                    | ✅     | ?      |
| - Compass                                                                       | 2      | 2      |
| - Scan                                                                          | ?      | ?      |
| - Celtic knot                                                                   | ?      | ✅     |
| - Slide                                                                         | ✅     | ✅     |
| - Towers                                                                        | ?      | ?      |
| Example app                                                                     | ✅     | ✅     |
| **AfkWarden**                                                                   | &nbsp; | &nbsp; |
| - Inactive                                                                      | 1      | ✅     |
| - XP Counter                                                                    | ❌     | ❌     |
| - Chatbox                                                                       | ✅     | ✅     |
| - Crafting menu                                                                 | ✅     | ✅     |
| - Buffs                                                                         | ✅     | ✅     |
| - Action bar stats                                                              | ✅     | ✅     |
| - Dialog box                                                                    | ✅     | ✅     |
| - Target death                                                                  | ?      | ?      |
| - Sheathe stance                                                                | ?      | ?      |
| - Castle Wars                                                                   | ?      | ?      |
| - Fight kiln waves                                                              | ?      | ?      |
| - Target death                                                                  | ?      | ?      |
| - Item drops                                                                    | ?      | ?      |
| **DgKey**                                                                       | &nbsp; | &nbsp; |
| - Show map                                                                      | ✅     | ?      |
| - Track key                                                                     | ❌     | ?      |
| - Select player location                                                        | ❌     | ?      |
| **[ArchMatCounter](https://zerogwafa.github.io/ArchMatCounter/appconfig.json)** | ?      | ?      |
| **Bank price checker**                                                          | ✅     | ?      |

- 1: Only keyboard activity count as active
- 2: Detected but cannot place pin

## Installation setup

These instructions are for those who have little/no programming experience and prepare your environment to run the instructions in the following section `Running`.

- [macOS](./docs/macos-setup.md)
  - [video guide](https://youtu.be/X03SyyV9Bro) from PupRS

## Running

This project use [Poetry](https://python-poetry.org) as package manager.

Requires Poetry 1.1.

```sh
# Try this first
poetry install
# If previous fails and you're on Big Sur, try this instead
SYSTEM_VERSION_COMPAT=1 poetry install

poetry build
cp build/lib.*/runekit/image/*.cpython*.* runekit/image/

# If you just want to load AFKWarden
poetry run python main.py https://runeapps.org/apps/alt1/afkscape/appconfig.json
# If you'd like to pick what app you load
poetry run python main.py
```

### Linux additional instruction

Requires libxcb to be installed

### macOS additional instruction

~~You'll probably need Command Line Tools to build the C code, run: `xcode-select --install` to get it~~ Currently the native code isn't really used (will be used for OCR features)

You will need to add Python in System Preferences > Security > Privacy in these sections:

- Accessibility
- Screen Recording

Note that Python might appear as the closest macOS application (eg. your terminal emulator) instead of Python

## Developer

Start with `--remote-debugging-port=9222` to enable remote debugger protocol.
To debug, go to `chrome://inspect` on Chrome/Chromium.

## Technical Features

- [Alt1 Compatibility](compatibility.md)

| Platform Feature        | Linux  | macOS  |
| ----------------------- | ------ | ------ |
| **Game Manager**        | &nbsp; | &nbsp; |
| Instance change signals | ❌     | ❌     |
| **Instance**            | &nbsp; | &nbsp; |
| alt1_pressed            | 1      | ✅     |
| game_activity           | 2      | ✅     |
| positionChanged         | ✅     | ✅     |
| scalingChanged          | ❌     | ❌     |
| focusChanged            | ✅     | ✅     |
| set_taskbar_progress    | ❌     | ❌     |
| Window capture          | ✅     | ✅     |

- 1: Works, but the game also receive the key
- 2: Only detect keyboard activity

## Known issues

- On macOS some values include the size of window decorator, including the screenshot
  - This can be tested with AfkScape color picker

## License

This project is [No Maintenance Intended](https://unmaintained.tech/).
It is provided as-is and may not be actively maintained. There's no support, and no promise that pull requests will be
reviewed and merged. In other word: I wrote this for my own use and there's no point in keeping it to myself so I'm sharing it.
However, maintaining it as a proper open source project is an ongoing work that I don't have the bandwidth to do.

This project is [licensed](LICENSE) under GPLv3, and contains code from [third parties](THIRD_PARTY_LICENSE.md).
Contains code from the Alt1 application.

Please do not contact Alt1 or RuneApps.org for support.
