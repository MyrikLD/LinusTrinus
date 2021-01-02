import socket
import struct
from dataclasses import dataclass
from logging import getLogger
from typing import Iterable, Union

from alvr_utils.packet import TrackingInfo
from utils.base_types import Quaternion, Vector3

log = getLogger(__name__)

RADIAN_IN_DEGREE = 57.29578


class Base:
    def format(self, f: str):
        return [self.__getattribute__(i) for i in f]

    @classmethod
    def parse(cls, data: Iterable, f: str):
        return cls(**dict(zip(f, data)))

    def radians(self):
        raise NotImplementedError()

    def degrees(self):
        raise NotImplementedError()


class QuaternionD(Base, Quaternion):
    def radians(self):
        return QuaternionR(
            self.w * RADIAN_IN_DEGREE,
            self.x * RADIAN_IN_DEGREE,
            self.y * RADIAN_IN_DEGREE,
            self.z * RADIAN_IN_DEGREE,
        )

    def degrees(self):
        return self


class QuaternionR(Base, Quaternion):
    def radians(self):
        return self

    def degrees(self):
        return QuaternionD(
            self.w / RADIAN_IN_DEGREE,
            self.x / RADIAN_IN_DEGREE,
            self.y / RADIAN_IN_DEGREE,
            self.z / RADIAN_IN_DEGREE,
        )


class Vector3D(Base, Vector3):
    def degrees(self):
        return self

    def radians(self):
        return Vector3R(
            self.x * RADIAN_IN_DEGREE,
            self.y * RADIAN_IN_DEGREE,
            self.z * RADIAN_IN_DEGREE,
        )


class Vector3R(Base, Vector3):
    def degrees(self):
        return Vector3D(
            self.x / RADIAN_IN_DEGREE,
            self.y / RADIAN_IN_DEGREE,
            self.z / RADIAN_IN_DEGREE,
        )

    def radians(self):
        return self


@dataclass
class Device:
    rotation: Union[QuaternionD, QuaternionR]
    position: Union[Vector3D, Vector3R]

    def pack(self):
        return struct.pack(
            "4d3d",
            *self.rotation.radians().format("wxyz"),
            *self.position.radians().format("xyz")
        )


class OpenVR:
    def __init__(self):
        self.addr = ("127.0.0.1", 4242)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.connect(self.addr)

    def callback(self, data: TrackingInfo):
        try:
            self.sock.sendto(data.pack(), self.addr)
        except:
            pass
