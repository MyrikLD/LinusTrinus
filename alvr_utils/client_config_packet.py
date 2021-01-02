import json
import struct

from pydantic import BaseModel

from alvr_utils.framer import Framer


class ClientConfigPacket(BaseModel):
    session_desc: dict
    eye_resolution_width: int
    eye_resolution_height: int
    fps: float
    web_gui_url: str
    reserved: str = ""

    def pack(self) -> bytes:
        payload = b""
        payload += Framer.encode(
            json.dumps(self.session_desc).replace(": ", ":").replace(", ", ",").encode()
        )

        payload += struct.pack("I", self.eye_resolution_width)
        payload += struct.pack("I", self.eye_resolution_height)
        payload += struct.pack("f", self.fps)

        payload += Framer.encode(self.web_gui_url.encode())
        payload += Framer.encode(self.reserved.encode())

        return struct.pack(">I", len(payload)) + payload
