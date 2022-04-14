# LinusTrinus

TrinusVR screen streaming server for Linux

## Available modes
#### Devices
- Mouse
- Steamvr
#### Screen capture
- ffmped
- xwd

## Dependencies

* Python3 / Pypy3
* evdev (optional)
* ffmpeg
* wand
* xwd
* xwininfo
* TrinusVR android client (tested on 2.2.1)

## Running

1. Start the TrinusVR Android client and configure it.
2. Press the start button in the TrinusVR Android client.
3. Run LinuxTrinus: `python3 main.py`

Detailed installation instructions in [INSTALL.md](INSTALL.md).

## Thanks

* [r57zone](https://github.com/r57zone/OpenVR-OpenTrack) - for good example
* [TrinusVR team](https://www.trinusvirtualreality.com/) - for android client
