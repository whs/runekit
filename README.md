# RuneKit

[![No Maintenance Intended](https://unmaintained.tech/badge.svg)](https://unmaintained.tech/)

Alt1-compatible toolbox for RuneScape 3, for Linux and macOS.

* [Compatibility](https://github.com/whs/runekit/wiki/App-Compatibility)
* [macOS installation guide](docs/macos-setup.md)

## Installing

### Linux

1. [Download RuneKit.AppImage](https://github.com/whs/runekit/releases/tag/continuous)
2. Mark file as executable (`chmod +x`)
3. Start the game
4. Run `RuneKit.AppImage`.
   - On first start it will download app list
5. Right click the tray icon and start any application

### macOS

1. [Download RuneKit.app](https://github.com/whs/runekit/releases) and unzip
2. Double click it
   - The first launch may takes a few minutes while macOS verify the application's security (we shipped a bunch of unused libraries - it is harder to remove them than to just ship it). The dock icon will keep bouncing while this is in progress
3. If permission prompt appears, grant it in System Preferences > Security. **Then quit RuneKit (right click dock icon > force quit) and start it again.** Don't quit RuneKit while it is downloading app list! The list of permissions are:
   - Accessibility - for access to game window
   - Input Monitoring - for hooking alt+1 and idle detection
   - Screen Recording - for capturing game
4. Once all permission has been granted the application appears as system tray icon

## Troubleshooting

[See wiki](https://github.com/whs/runekit/wiki/Troubleshooting)

## Developer

This project use [Poetry](https://python-poetry.org) as package manager.

Requires Poetry 1.1.

```sh
poetry install
# If previous fails and you're on Big Sur, try this instead
SYSTEM_VERSION_COMPAT=1 poetry install

poetry run make dev

# If you just want to load AFKWarden
poetry run python main.py https://runeapps.org/apps/alt1/afkscape/appconfig.json
# If you'd like to pick what app you load
poetry run python main.py
```

Start with `--remote-debugging-port=9222` to enable remote debugger protocol.
To debug, go to `chrome://inspect` on Chrome/Chromium.

### Building .app on Mac

1. Run the normal build steps
2. XCode > Settings > Account and download your dev key
   - I don't have paid Apple Developer CA to test
3. Set codesign_identity in  RuneKit.spec or leave it None for ad-hoc sign
5. `poetry run make dist/RuneKit.app.zip`

## License

This project is [No Maintenance Intended](https://unmaintained.tech/).
It is provided as-is and may not be actively maintained. There's no support, and no promise that pull requests will be
reviewed and merged. In other word: I wrote this for my own use and there's no point in keeping it to myself so I'm sharing it.
However, maintaining it as a proper open source project is an ongoing work that I don't have the bandwidth to do.

This project is [licensed](LICENSE) under GPLv3, and contains code from [third parties](THIRD_PARTY_LICENSE.md).
Contains code from the Alt1 application.

Please do not contact Alt1 or RuneApps.org for support.
