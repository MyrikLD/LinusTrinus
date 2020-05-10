import base64
import hashlib
import json
import logging
import socket
import struct
from pprint import pformat
from threading import Thread

from drop_queue import DropQueue

log = logging.getLogger(__name__)


class Sender(Thread):
    end = False
    buffer_size = 1024

    def __init__(self, server, client_port=7777, server_port=5555):
        Thread.__init__(self)
        self.sock, self.settings = self.create_sock(server, client_port, server_port)

        self.framebuf = DropQueue(2)

    def create_sock(self, server, client_port=7777, server_port=5555):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, client_port))

        sett = self.get_settings(sock)

        log.info(pformat(sett))

        settings = json.dumps(
            {
                "version": "std2",
                "code": self.ch_summ(sett["ref"], "_defaulttglibva"),
                "videostream": "mjpeg",
                "sensorstream": "normal",
                "sensorport": server_port,
                "sensorVersion": 1,
                "motionboost": False,
                "nolens": False,
                "convertimage": False,
                "fakeroll": False,
                "source": "None",
                "project": "Python",
                "proc": "None",
                "stroverlay": "",
            }
        ).encode("utf-8")

        sock.send(settings)

        return sock, sett

    def run(self):
        while not self.end:
            self.recv()

    def send(self):
        scr = self.framebuf.get()
        self.sock.send(struct.pack(">i", len(scr)))
        self.sock.send(scr)

    def recv(self):
        try:
            t = self.sock.recv(1)
            for i in range(t.count(b"e")):
                self.send()
        except ConnectionResetError:
            log.info("Connection closed")
            self.end = True

    @staticmethod
    def ch_summ(ref, module):
        c = ref + module
        a = hashlib.sha1(c.encode("utf-8"))
        s = a.digest()
        c = base64.b64encode(s).decode("utf-8") + module
        return c

    def get_settings(self, sock: socket.socket):
        settings = json.loads(sock.recv(self.buffer_size).decode("utf-8"))
        settings["videoSupport"] = settings["videoSupport"].split(",")
        settings["sensorSupport"] = settings["sensorSupport"].split(",")
        return settings
