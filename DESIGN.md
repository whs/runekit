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

### Image format
The library has two internal image formats:

- numpy.ndarray of shape (height, width, 4)
  - Current standard
  - Store pixels in BGRA32 format (ARGB 8 bit per channel in little endian)
  - Should be faster as no channel swapping is needed
  - Requires copying when accessing raw buffer
  - Support OpenCV operation
- PIL Image
  - Deprecated
  - Store pixels in RGBA32 format
  - Slower as when communicating with Alt1 we need to swap to BGRA
  - Can access raw buffer without copying
  - Easier to work with for basic operations

## App

Packages related to Alt1 app.

- alt1: Contains tools to work with Alt1 app schema (move this to app??)
- app: Wrap an Alt1 app instance
  - app.view: Qt views related to app
- browser: API exposed to QtWebEngine (move this to app.browser_profile??)

## UI

- host: RuneKit Qt root
- ui: Collection of UI tools

## Porting

With this design it should be simple to port RuneKit to any platform supported by Qt by just reimplementing `game` for that platform

# Settings design
- apps/
  - <b2b size 16 of manifest url> (json): App manifest
  - _folder
    - <folder name>/0 (str): App ID
  - _meta
    - isDefaultLoaded (bool): Has default apps list downloaded
