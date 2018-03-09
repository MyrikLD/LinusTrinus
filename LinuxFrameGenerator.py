import subprocess
from threading import Thread
from DropQueue import DropQueue


class FrameGenerator(Thread):
    size = '1920x1080'
    # size = '640x480'
    framerate = 60
    optirun = False
    vsync = 2

    def __init__(self, settings: dict, buf: DropQueue):
        super(FrameGenerator, self).__init__()
        self.framebuf = buf
        self.settings = settings
        self.end = False

    @staticmethod
    def api(optirun=False, **kwargs) -> str:
        cmd = 'ffmpeg -f x11grab'
        if optirun:
            cmd = 'optirun ' + cmd
        for i in kwargs.items():
            cmd += ' -%s %s' % i
        cmd += ' -'
        return cmd

    def run(self):
        params = {
            'loglevel': 'error',
            's': self.size,
            'framerate': self.framerate,
            'i': ':0.0',
            # 'qmin:v': 19,
            'f': 'mjpeg',
            'vsync': self.vsync,
            # 'vf': 'scale=1280x1024'
        }
        ffmpeg_cmd = self.api(self.optirun, **params)
        print(ffmpeg_cmd)
        p = subprocess.Popen(ffmpeg_cmd.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

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
