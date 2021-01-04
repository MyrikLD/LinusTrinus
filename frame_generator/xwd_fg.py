import fcntl
import os
import re
import subprocess
from logging import getLogger
from threading import Thread

from wand.image import Image

from drop_queue import DropQueue

log = getLogger(__name__)


def output(p):
    l = True
    while l:
        l = p.readline()
        print(l)


class XwdFrameGenerator(Thread):
    end = False
    framebuf: DropQueue

    def __init__(self, buf: DropQueue):
        super().__init__()
        self.framebuf = buf

    @staticmethod
    def find_window_id(name: str) -> int:
        p = subprocess.Popen(
            f'xwininfo -name "{name}"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        text = p.communicate()[0]
        window_id = re.findall(r"Window id: 0x([\da-f]+)", text.decode())
        if window_id:
            return int(window_id[0], 16)

    @staticmethod
    def get_xwd(window_id: int) -> bytes:
        p = subprocess.Popen(
            f"xwd -id {hex(window_id)}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        data = p.communicate()

        if data[0]:
            return data[0]

    def run(self):
        p = subprocess.Popen(
            "ffmpeg -i pipe: -an -f mjpeg -c:v libx265 -flush_packets 1 -vf scale=2880:1600 -",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )

        fcntl.fcntl(
            p.stdout.fileno(),
            fcntl.F_SETFL,
            fcntl.fcntl(p.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,
        )

        self.end = False
        window_id = None
        log.info("Waiting for compositor window")
        while not window_id:
            window_id = self.find_window_id("SteamVR Compositor")
        log.info("Found compositor window id: %s", hex(window_id))

        while not self.end:
            data = self.get_xwd(window_id)

            if not data:
                continue

            try:
                with Image(blob=data, format="xwd") as im:
                    # im.resize(2880, 1600)
                    # output(p.stderr)
                    p.stdin.write(im.make_blob("jpg"))

                    d = p.stdout.read()
                    if d:
                        # with open("o.mp4", "ab") as f:
                        #     f.write(d)
                        self.framebuf.put(d)
            except:
                print("error")

        log.info("FrameGenerator end")
