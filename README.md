# RuneKit

[![No Maintenance Intended](https://unmaintained.tech/badge.svg)](https://unmaintained.tech/)

Alt1-compatible toolbox for RuneScape 3, for Linux and macOS.

* [Compatibility](https://github.com/whs/runekit/wiki/App-Compatibility)
* [macOS installation guide](docs/macos-setup.md)

## Running

This project use [Poetry](https://python-poetry.org) as package manager.

Requires Poetry 1.1.

```sh
# Try this first
poetry install
# If previous fails and you're on Big Sur, try this instead
SYSTEM_VERSION_COMPAT=1 poetry install

poetry run make dev

# If you just want to load AFKWarden
poetry run python main.py https://runeapps.org/apps/alt1/afkscape/appconfig.json
# If you'd like to pick what app you load
poetry run python main.py
```

### Linux additional instruction

Requires libxcb to be installed

### macOS additional instruction

You will need to add Python in System Preferences > Security > Privacy in these sections:

- Accessibility
- Screen Recording

Note that Python might appear as the closest macOS application (eg. your terminal emulator) instead of Python

## Developer

Start with `--remote-debugging-port=9222` to enable remote debugger protocol.
To debug, go to `chrome://inspect` on Chrome/Chromium.

## License

This project is [No Maintenance Intended](https://unmaintained.tech/).
It is provided as-is and may not be actively maintained. There's no support, and no promise that pull requests will be
reviewed and merged. In other word: I wrote this for my own use and there's no point in keeping it to myself so I'm sharing it.
However, maintaining it as a proper open source project is an ongoing work that I don't have the bandwidth to do.

This project is [licensed](LICENSE) under GPLv3, and contains code from [third parties](THIRD_PARTY_LICENSE.md).
Contains code from the Alt1 application.

Please do not contact Alt1 or RuneApps.org for support.
