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

* [ffmpeg](https://command-not-found.com/ffmpeg)
* [xwininfo](https://command-not-found.com/xwininfo)
* [xwd](https://command-not-found.com/xwd)
* Python3 / Pypy3
* Python packages:
    * [wand](https://pypi.org/project/Wand/)
    * [evdev](https://pypi.org/project/evdev/) (optional)
* [TrinusVR](https://www.trinusvirtualreality.com/) Android client (tested on 2.2.1)

## Running

1. Start the TrinusVR Android client and configure it.
2. Press the start button in the TrinusVR Android client.
3. Run LinuxTrinus: `python3 main.py`

Detailed installation instructions in [INSTALL.md](INSTALL.md).

## Thanks

* [r57zone](https://github.com/r57zone/OpenVR-OpenTrack) - for good example
* [TrinusVR team](https://www.trinusvirtualreality.com/) - for android client
