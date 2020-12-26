import re
import subprocess
from logging import getLogger
from threading import Thread

from wand.image import Image

from drop_queue import DropQueue

log = getLogger(__name__)


class XwdFrameGenerator(Thread):
    end = False
    framebuf: DropQueue

    def __init__(self, settings: dict, buf: DropQueue):
        super().__init__()
        self.framebuf = buf
        self.settings = settings

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
        self.end = False
        window_id = None
        while not window_id:
            window_id = self.find_window_id("SteamVR Compositor")
        log.info("Found compositor window id: %s", hex(window_id))

        while not self.end:
            data = self.get_xwd(window_id)

            if not data:
                continue

            with Image(blob=data, format="xwd") as im:
                self.framebuf.put(im.make_blob("jpeg"))

        log.info("FrameGenerator end")
