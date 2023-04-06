import os
import subprocess
from logging import getLogger
from threading import Thread

from drop_queue import DropQueue

log = getLogger(__name__)


class FfmpegDoubleFrameGenerator(Thread):
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

    @property
    def size2width(self):
        return f"{self.width*2}x{self.height}"

    @staticmethod
    def api(optirun=False, params=None, **kwargs) -> str:
        cmd = "ffmpeg"
        if optirun:
            cmd = "optirun " + cmd
        for i in params:
            cmd += f" -{i[0]} {i[1]}"
        cmd += " -"
        return cmd

    def _get_frame(self, data, start, end):
        frame = data[start:end]
        return frame

    def _get_display(self):
        # Or try :0.0
        # return ":0.0"
        return os.getenv("DISPLAY", ":0.0") + "+0,0"

    def run(self):
        """
        Run ffmpeg stream video in pipe , should run some like:
        ffmpeg  -f lavfi -i color=white:s=2732x768\
                -f x11grab -video_size 1366x768 -framerate 30 -i :0.0 \
                -f x11grab -video_size 1366x768 -framerate 30 -i :0.0 \
                -filter_complex "overlay,overlay=1366:0" \
                -vcodec libx264 test.mkv
        Ordering of command parametrs IMPOTANT
        """

        self.end = False
        params = [
            ("f", "lavfi"),
            ("i", f"color=white:s={self.size2width}"),
            ("f", "x11grab"),
            ("video_size", self.size),
            ("framerate", self.framerate),
            ("i", self._get_display()),
            ("f", "x11grab"),
            ("video_size", self.size),
            ("framerate", self.framerate),
            ("i", self._get_display()),
            ("filter_complex", f'"overlay,overlay={self.width}:0"'),
            ("loglevel", "error"),
            ("nostdin", ""),
            ("s", self.size),
            ("framerate", self.framerate),
            ("f", "mjpeg"),
            # ("vsync", self.vsync),
        ]
        ffmpeg_cmd = self.api(self.optirun, params)
        log.info(f"ffmpeg cmd: {ffmpeg_cmd}")
        p = subprocess.Popen(
            ffmpeg_cmd.split(),
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )

        data = bytearray()
        start = -1
        cnt = 0
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
                log.info(f"frame: {cnt}")
                cnt = cnt + 1
                data = data[end + 2 :]
                start = -1
        log.info("DoubleFrameGenerator end")
