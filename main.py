import asyncore
import base64
import hashlib
import json
import socket
import struct
from threading import Thread
from time import sleep

from Discover import discover
from DropQueue import DropQueue
from LinuxFrameGenerator import FrameGenerator
from OpenVR_callback import OpenVR

try:
    from pprint import pprint
except ImportError:
    pprint = print

TCP_IP = discover()
TCP_PORT = 7777
SENSOR_PORT = 5555
BUFFER_SIZE = 1024


class SensorClient(Thread, asyncore.dispatcher):
    data = None

    def __init__(self, callback_objects=list()):
        Thread.__init__(self)
        asyncore.dispatcher.__init__(self)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((TCP_IP, SENSOR_PORT))

        self.callback = [i.callback for i in callback_objects]

    def run(self):
        asyncore.loop()

    def handle_read(self):
        self.on_data(self.recv(BUFFER_SIZE))

    def on_data(self, data):
        self.data = self.decode_pos(data)

        if self.data:
            for i in self.callback:
                i(self.data)

    @staticmethod
    def sensor_31(data):
        # empty = struct.unpack('b4b4b4b', data[:13])
        dt = struct.unpack('3f', data[13:25])
        speed = struct.unpack('6b', data[-6:])
        return {'data': dt, 'speed': speed}

    @staticmethod
    def sensor_53(data):
        crc, _, trigger = struct.unpack('3b', data[:3])
        speed = struct.unpack('2b', data[3:5])
        axisXY = struct.unpack('2f', data[5:13])
        eulerData = struct.unpack('3f', data[13:25])
        quaternion = struct.unpack('4f', data[25:41])
        accel = struct.unpack('3f', data[41:])
        return {'trigger': trigger,
                'speed': speed,
                'axisXY': axisXY,
                'eulerData': eulerData,
                'quaternion': quaternion,
                'accel': accel}

    def decode_pos(self, data):
        data_len = len(data)
        if not data_len % 53:
            return self.sensor_53(data[-53:])
        elif not data_len % 31:
            return self.sensor_31(data[-31:])
        else:
            print('WARNING: Unknown sensor data len: %i' % data_len)

    @staticmethod
    def split_list(lst, group_len):
        l = len(lst)
        kol_in_group = l // group_len
        return [lst[i:i + kol_in_group] for i in range(0, l, kol_in_group)]


class Sender(Thread):
    end = False

    def __init__(self):
        Thread.__init__(self)
        self.sock, self.settings = self.create_sock()

        self.framebuf = DropQueue(2)

    def create_sock(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TCP_IP, TCP_PORT))

        sett = self.get_settings(sock)

        pprint(sett)

        settings = json.dumps({
            "version": 'std2',
            "code": self.ch_summ(sett['ref'], '_defaulttglibva'),
            "videostream": 'mjpeg',
            "sensorstream": 'normal',
            "sensorport": SENSOR_PORT,
            "sensorVersion": 1
        }).encode('utf-8')

        sock.send(settings)

        return sock, sett

    def run(self):
        while not self.end:
            self.recv()

    def send(self):
        scr = self.framebuf.get()
        self.sock.send(struct.pack('>i', len(scr)))
        self.sock.send(scr)

    def recv(self):
        try:
            t = self.sock.recv(1)
            for i in range(t.count(b'e')):
                self.send()
        except ConnectionResetError:
            print('Connection closed')
            self.end = True

    @staticmethod
    def ch_summ(ref, module):
        c = ref + module
        a = hashlib.sha1(c.encode('utf-8'))
        s = a.digest()
        c = base64.b64encode(s).decode('utf-8') + module
        return c

    @staticmethod
    def get_settings(sock):
        settings = json.loads(sock.recv(BUFFER_SIZE).decode("utf-8"))
        settings['videoSupport'] = settings['videoSupport'].split(',')
        settings['sensorSupport'] = settings['sensorSupport'].split(',')
        return settings


if __name__ == '__main__':
    sender = Sender()

    # Run frame generator for sender
    framegen = FrameGenerator(sender.settings, sender.framebuf)
    framegen.start()

    # Start sending frames to client
    sender.start()

    # Wait for sensor server init
    sleep(1)

    openvr = OpenVR()

    client = SensorClient([openvr])
    client.start()

    client.join()
    sender.join()
    framegen.join()
