import socket
import struct
from logging import getLogger

log = getLogger(__name__)


class OpenVR:
    def __init__(self):
        self.addr = ("127.0.0.1", 4242)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.connect(self.addr)

    def callback(self, data):
        if "quaternion" not in data:
            return
        q = data["quaternion"]
        d = 57.29578  # 1 radian in degrees
        log.debug('q: %s', q)
        # WXYZ
        packet = struct.pack("4d", q[3] / d, q[0] / -d, q[1] / -d, q[2] / d)
        try:
            self.sock.sendto(packet, self.addr)
        except:
            pass
