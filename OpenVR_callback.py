import socket
import struct


class OpenVR:
    def __init__(self):
        self.addr = ("127.0.0.1", 4242)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.connect(self.addr)

    def callback(self, data):
        prepare = -data['eulerData'][2], -data['eulerData'][0], -data['eulerData'][1]
        packet = struct.pack('6d', 0,0,0, *prepare)
        try:
            self.sock.sendto(packet, self.addr)
        except:
            pass
