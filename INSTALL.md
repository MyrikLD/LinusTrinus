Time required      | Difficulty    | Last update
 ---               | ---           | ---
:hourglass: 15-20m | :baby: newbie | :date: Nov, 2021

---

# Installation guide

Step by step instructions tested on Manjaro. I'm using terminal so that aside of
package manager and package names these instructions wouldn't differ much from
other Linux distributions.


## Tether phone to computer

To begin you need a working connection between Android and your Linux PC. For
that a USB tethering is preferable. Bluetooth tethering is too slow for image
transfer. You can use WiFi tethering but it will be considerably slower and,
unless your phone has two WiFi modules, the only Internet connection available
for your PC while the phone stays connected will be your phone's data plan.

1. In terminal:
    ```sh
    $ nmcli d            # d = devices
    DEVICE   TYPE      STATE         CONNECTION
    enp0s1   ethernet  connected        #<< my active network device
    wlp3s0   wifi      unavailable   --
    ```
1. Connect phone to PC via USB 3.0 data transfer cable

    ---
    > :bulb: Not all charging cables are data transfer cables

    > :warning: Set phone to **WiFi only** or Tux will eat all your dataplan fishes!
    ---

1. In phone's settings find `USB tethering` and turn it on:

    <img src="https://user-images.githubusercontent.com/6132708/141599346-bfe0a541-52ed-4bc3-b736-8446bd2d5cd4.png" width="25%">

1. In terminal:
    ```sh
    $ nmcli d
    DEVICE   TYPE      STATE         CONNECTION
    enp0s1   ethernet  connected     (...)
    enp0s2   ethernet  disconnected     #<< new network device
    wlp3s0   wifi      unavailable   --

    $ nmcli d c enp0s2   # d = device, c = connect

    $ nmcli d
    DEVICE   TYPE      STATE         CONNECTION
    enp0s1   ethernet  disconnected  (...)
    enp0s2   ethernet  connected        #<< new network device is active
    wlp3s0   wifi      unavailable   --
    ```

    ---
    > :heavy_check_mark: Done! Your your phone is now tethered to your PC! Your PC connects to the Internet through your phone.

    > :warning: Remember to **switch connection back to step 1** when you're done!
    ---


## Install and run VR


### Server

1. In terminal install system dependencies:
    ```sh
    pacman -S git python3 make cmake gcc glew qt5-base imagemagick # if you are on a fresh install e.g. inside Distrobox
    pacman -S ffmpeg openvr
    pacman -S xorg-xwd xorg-xwininfo   # for Ubuntu: `sudo apt install x11-apps`
    ```
1. clone this repo:
    ```sh
    cd ~/projects                   # or wherever you keep your repos
    git clone --depth 1 https://github.com/MyrikLD/LinusTrinus
    cd LinusTrinus
    ```
1. Install Python dependencies:
    ```sh
    python3 -m venv .venv           # optional to install locally
    source .venv/bin/activate       # and not in `/usr/lib/python*/blah/...`
    pip install frame-generator wand
    ```
1. Bind mount the SteamVR directory to the default Steam install directory, if you have it installed elsewhere:
    ```sh
    mount --bind <SteamVR_install_directory> "$HOME/.steam/steam/common/SteamVR"
    ```
1. Compile and install driver for SteamVR:
    ```sh
    cd samples
    ./make.sh
    cd ..
    ```
1. Run server:
    ```sh
    python3 main.py                 # with virtual environment still active
    ```

    ---
    > :bulb: After you're done, stop by pressing <kbd>ctrl</kbd>+<kbd>c</kbd> twice
    > and close the terminal or call a `deactivate` command to disable venv.
    ---


### Client

1. Install [Trinus CBVR Lite](https://play.google.com/store/apps/details?id=com.loxai.trinus.test) on your phone
1. Run the app and set what you want
1. Make sure tethering is active (app detects USB connection)
1. Touch the power button icon

    ---
    > :heavy_check_mark: Success! Terminal went bananas and phone screen is black!
    ---


### Steam

1. Make sure your server is running in an activated virtual environment
1. Make sure:
    - your phone is connected
    - tethering is enabled
    - tethered network device is active
    - client app is started and connected
1. Run Steam and SteamVR - enjoy!

    ---
    > :warning: Remember to **switch your Internet connection back** when you're done!
    ---


## Known culprits

* VR headset not waking up

    If Steam complains about your VR headset being in standby try switching sensor
    modes in the mobile app's settings. Mode `A` works well for Xiaomi phones.

* Phone/head too big/small

    Unfortunately your Android device and Google Cardboard have to be compatible
    because VR client app doesn't have a calibration option and doesn't use external
    calibration apps like other Google Cardboard compatible apps. Lens correction
    option is buggy on Xiaomi Poco X3 Pro - it renders both eyes squeezed on the
    bottom half of the screen.

* Phone transfer mode

    After connecting USB your phone will ask for transfer mode, be it file transfer
    or some different method. Dismiss that dialogue as selecting anything here will
    disable tethering.

* App not detecting tethering

    Sometimes after changing options in the mobile app it doesn't detect USB
    connection. Usually pressing a back button once helps.

* Please plug in your VR headset

    If your phone connects to the server (black screen) but Steam doesn't detect VR
    device you've probably forgotten to compile the driver as described in [Server](#server).

* SteamVR hunging

    It sometimes looks like it hung but really it didn't and you can just restart
    the server and re-run the app on your phone, then focus SteamVR and everything
    will reconnect. Free version of Trinus CBVR only works for 15 miniutes at a time
    anyway so you'll reconnect often.

    LinusTrinus server works by cloning part of the screen to your phone through
    OpenVR. It's slow. SteamVR can draw directly to VR device but this server
    doesn't seem to support it. Steam will often ask to switch to this direct
    drawing mode but if you do it *will hung* during SteamVR restart.
