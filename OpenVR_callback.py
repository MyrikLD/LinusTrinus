import socket
import struct


class OpenVR:
    def __init__(self):
        self.addr = ("127.0.0.1", 4242)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.connect(self.addr)

    def callback(self, data):
        if not 'eulerData' in data:
            return
        # prepare = data['eulerData'][2], data['eulerData'][0], data['eulerData'][1]
        q = data['quaternion']
        d = 57.29578
        print(q)
        packet = struct.pack('4d', q[0]/-d, q[1]/-d, q[2]/d, q[3]/d)
        try:
            self.sock.sendto(packet, self.addr)
        except:
            pass
