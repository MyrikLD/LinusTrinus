# LinusTrinus

TrinusVR screen streaming server for Linux

## Modes
|      Configuration      |   Status  |
| ----------------------- |:---------:|
| Mouse                   |   OK      |
| SteamVR / OpenVR        |   OK      |
| Raw output              |   OK      |
| ???                     |   !!!     |


## Dependencies

* Python3 / Pypy3
* evdev (optional)
* ffmpeg
* TrinusVR android client (tested on 2.2.1)

## Running

1. Start the TrinusVR Android client and configure it.
2. Press the start button in the TrinusVR Android client.
3. Run LinuxTrinus: `python3 main.py`

## Thanks

* [r57zone](https://github.com/r57zone/OpenVR-OpenTrack) - for good example
* [TrinusVR team](https://www.trinusvirtualreality.com/) - for android client