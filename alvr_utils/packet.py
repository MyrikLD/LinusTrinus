from enum import Enum, Flag
from typing import Tuple

import rawutil
from pydantic import BaseModel, validator
from pydantic.dataclasses import dataclass

from utils.base_types import Quaternion, Vector2, Vector3


def parse_packet(data):
    type_id = rawutil.unpack("I", data)[0]
    t = ALVRPacketType.get_type(type_id)
    if t:
        return t.unpack(data)


class ControllerFlags(Flag):
    ENABLE = 1 << 0
    LEFTHAND = 1 << 1  # 0: Left hand, 1: Right hand
    GEARVR = 1 << 2
    OCULUS_GO = 1 << 3
    OCULUS_QUEST = 1 << 4
    OCULUS_HAND = 1 << 5

    def to_bytes(self, *args, **kwargs):
        return int(self.value).to_bytes(*args, **kwargs)


class ALVRPacketType(int, Enum):
    HELLO_MESSAGE = 1
    CONNECTION_MESSAGE = 2
    RECOVER_CONNECTION = 3
    BROADCAST_REQUEST_MESSAGE = 4
    STREAM_CONTROL_MESSAGE = 5
    TRACKING_INFO = 6
    TIME_SYNC = 7
    CHANGE_SETTINGS = 8
    VIDEO_FRAME = 9
    AUDIO_FRAME_START = 10
    AUDIO_FRAME = 11
    PACKET_ERROR_REPORT = 12
    HAPTICS = 13
    MIC_AUDIO = 14
    GUARDIAN_SYNC_START = 15
    GUARDIAN_SYNC_ACK = 16
    GUARDIAN_SEGMENT_DATA = 17
    GUARDIAN_SEGMENT_ACK = 18

    @classmethod
    def get_type(cls, type_id: "ALVRPacketType"):
        tr = {cls.TRACKING_INFO: TrackingInfo, cls.VIDEO_FRAME: VideoFrame}
        return tr.get(type_id)


class TrackingQuat(Quaternion):
    @classmethod
    def struct(cls):
        return rawutil.Struct("4f").format


class TrackingVec3(Vector3):
    @classmethod
    def struct(cls):
        return rawutil.Struct("3f").format


class TrackingVec2(Vector2):
    @classmethod
    def struct(cls):
        return rawutil.Struct("2f").format


@dataclass(frozen=True)
class EyeFov:
    left: float = 49.0
    right: float = 45.0
    top: float = 50.0
    bottom: float = 48.0

    @classmethod
    def struct(cls):
        return rawutil.Struct("4f").format

    def __iter__(self):
        for i in self.__annotations__:
            yield self.__getattribute__(i)

    def __getitem__(self, i):
        return tuple(self).__getitem__(i)


@dataclass(frozen=True)
class FingerPinchStrengths:
    index: float
    middle: float
    ring: float
    pinky: float

    @classmethod
    def struct(cls):
        return rawutil.Struct("4f").format

    def __iter__(self):
        for i in self.__annotations__:
            yield self.__getattribute__(i)

    def __getitem__(self, i):
        return tuple(self).__getitem__(i)


class Controller(BaseModel):
    flags: ControllerFlags
    buttons: int
    trackpad_position: TrackingVec2

    trigger_value: float
    grip_value: float

    batteryPercentRemaining: int
    recenter_count: int

    orientation: TrackingQuat
    position: TrackingVec3
    angular_velocity: TrackingVec3
    linear_velocity: TrackingVec3
    angular_acceleration: TrackingVec3
    linear_acceleration: TrackingVec3

    bone_rotations: Tuple[TrackingQuat, ...]  # 19
    bone_positions_base: Tuple[TrackingVec3, ...]  # 19

    bone_root_orientation: TrackingQuat
    bone_root_position: TrackingVec3

    input_state_status: int
    finger_pinch_strengths: FingerPinchStrengths
    hand_finger_confidences: int

    @classmethod
    def struct(cls):
        return rawutil.Struct(
            f"I Q ({TrackingVec2.struct()}) f f B B "
            f"({TrackingQuat.struct()}) "
            f"({TrackingVec3.struct()}) "
            f"({TrackingVec3.struct()}) "
            f"({TrackingVec3.struct()}) "
            f"({TrackingVec3.struct()}) "
            f"({TrackingVec3.struct()}) "
            f"19[{TrackingQuat.struct()}] "
            f"19[{TrackingVec3.struct()}] "
            f"({TrackingQuat.struct()}) "
            f"({TrackingVec3.struct()}) "
            f"I (4f) I"
        ).format

    def __iter__(self):
        for k in self.__fields__:
            v = self.__getattribute__(k)
            yield v

    def __getitem__(self, i):
        return tuple(self).__getitem__(i)


# @dataclass
class TrackingInfo(BaseModel):
    class Config:
        orm_mode = True

    type: ALVRPacketType = ALVRPacketType.TRACKING_INFO
    # flag_other_tracking_source: int
    flags: int

    client_time: int
    frame_index: int
    predicted_display_time: int

    headpose_pose_orientation: TrackingQuat
    headpose_pose_position: TrackingVec3

    other_tracking_source_position: TrackingVec3
    other_tracking_source_orientation: TrackingQuat

    eye_fov: Tuple[EyeFov, EyeFov]
    ipd: float
    battery: int

    controller: Tuple[Controller, Controller]

    @validator("controller", each_item=True, pre=True)
    def ControllerV(cls, v):
        if isinstance(v, list):
            return dict(zip(Controller.__fields__, v))
        return v

    @classmethod
    def struct(cls):
        return rawutil.Struct(
            f"I I Q Q d "
            f"({TrackingQuat.struct()}) ({TrackingVec3.struct()}) "
            f"({TrackingVec3.struct()}) ({TrackingQuat.struct()}) "
            f"2[{EyeFov.struct()}] "
            f"f Q 2[{Controller.struct()}]",
        ).format

    @classmethod
    def unpack(cls, data):
        result = rawutil.unpack(cls.struct(), data, names=list(cls.__fields__))
        return cls.from_orm(result)

    def __iter__(self):
        for k in self.__fields__:
            v = self.__getattribute__(k)
            yield v

    def pack(self):
        return rawutil.pack(self.struct(), *self)


class VideoFrame(BaseModel):
    class Config:
        orm_mode = True

    type: ALVRPacketType = ALVRPacketType.VIDEO_FRAME
    packetCounter: int
    trackingFrameIndex: int
    videoFrameIndex: int
    sentTime: int
    frameByteSize: int
    fecIndex: int
    fecPercentage: int

    @classmethod
    def struct(cls):
        return rawutil.Struct(f"I I Q Q Q I I H").format

    @classmethod
    def unpack(cls, data):
        result = rawutil.unpack(cls.struct(), data, names=list(cls.__fields__))
        return cls.from_orm(result)

    def __iter__(self):
        for k in self.__fields__:
            v = self.__getattribute__(k)
            yield v

    def pack(self):
        return rawutil.pack(self.struct(), *self)

