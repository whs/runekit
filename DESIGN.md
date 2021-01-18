# Package design

## Glossary

- Application: native application
- App: Alt1 application
- Platform: Windows, Linux, macOS
- Platform-dependent: Code that cannot run on other platforms without porting. Native code that can be run on all platform (without platform checks) are not considered platform-dependent

## Game tools

The `game` package is the only one allowed to use platform-dependent code. All other packages should use Qt functionalities, or put the code in this package.

- game: Interact with the game window. Since accessing other application's window is not abstracted by Qt, this package is the only one allowed to be platform dependent 
- image: Image processing tools

## App

Packages related to Alt1 app.

- alt1: Contains tools to work with Alt1 app schema (move this to app??)
- app: Wrap an Alt1 app instance
  - app.view: Qt views related to app
- browser: API exposed to QtWebEngine (move this to app.browser_profile??)

## UI

- host: Main window of RuneKit
- ui: Collection of UI tools

## Porting

With this design it should be simple to port RuneKit to any platform supported by Qt by just reimplementing `game` for that platform
