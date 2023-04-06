import os
import subprocess
from logging import getLogger
from threading import Thread

from drop_queue import DropQueue

log = getLogger(__name__)


class FfmpegFrameGenerator(Thread):
    end = False
    framebuf: DropQueue

    width = 1366
    height = 768

    framerate = 30
    optirun = False
    vsync = 2

    buffer_size = 1024 * 10

    def __init__(self, settings: dict, buf: DropQueue):
        super().__init__()
        self.framebuf = buf
        self.settings = settings

    @property
    def size(self):
        return f"{self.width}x{self.height}"

    @staticmethod
    def api(optirun=False, **kwargs) -> str:
        cmd = "ffmpeg -f x11grab"
        if optirun:
            cmd = "optirun " + cmd
        for i in kwargs.items():
            cmd += " -%s %s" % i
        cmd += " -"
        return cmd

    def run(self):
        self.end = False

        params = {
            "loglevel": "error",
            "s": self.size,
            "framerate": self.framerate,
            "i": "%s+0,0" % os.getenv("DISPLAY", ":0.0"),
            "f": "mjpeg",
            "vsync": self.vsync,
        }
        ffmpeg_cmd = self.api(self.optirun, **params)
        log.info("ffmpeg cmd: %s", ffmpeg_cmd)
        p = subprocess.Popen(
            ffmpeg_cmd.split(),
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )

        data = bytearray()
        start = -1
        while not self.end:
            data += p.stdout.read(self.buffer_size)

            if start == -1:
                start = data.find(b"\xFF\xD8\xFF")
                continue
            else:
                end = data.find(b"\xFF\xD9")

            if end != -1 and start != -1:
                frame = data[start : end + 1]
                self.framebuf.put(frame)

                data = data[end + 2 :]
                start = -1

        log.info("FrameGenerator end")
