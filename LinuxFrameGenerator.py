import subprocess
from threading import Thread
from DropQueue import DropQueue


class FrameGenerator(Thread):
    def __init__(self, settings: dict, buf: DropQueue):
        super(FrameGenerator, self).__init__()
        self.framebuf = buf
        self.settings = settings
        self.end = False

    @staticmethod
    def api(**kwargs) -> str:
        cmd = 'optirun ffmpeg -f x11grab'
        for i in kwargs.items():
            cmd += ' -%s %s' % i
        cmd += ' -'
        return cmd

    def run(self):
        params = {
            'loglevel': 'error',
            # 's': '1920x1080',
            's': '640x480',
            'framerate': 60,
            'i': ':8.0',
            # 'qmin:v': 19,
            'f': 'mjpeg',
            'vsync': 2,
            # 'vf': 'scale=1280x1024'
        }
        ffmpeg_data = self.api(**params)
        print(ffmpeg_data)
        p = subprocess.Popen(ffmpeg_data.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

        while not self.end:
            data = b''
            fc = 0

            for i in p.stdout:
                data += i
                start = data.find(b'\xFF\xD8\xFF')
                if start != -1:
                    end = data.find(b'\xFF\xD9')
                else:
                    # No end without start
                    continue
                if end != -1 and start != -1:
                    fc += 1
                    frame = data[start:end + 1]
                    self.framebuf.put(frame)

                    data = data[end + 2:]

        print('FrameGenerator end')
