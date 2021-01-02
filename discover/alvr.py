import socket
from logging import getLogger
from struct import unpack

from pydantic import BaseModel

from alvr_utils.framer import Framer

log = getLogger(__name__)


class ClientHandshake(BaseModel):
    alvr_name: str
    version: str
    device_name: str
    hostname: str
    certificate_pem: str
    reserved: str = ''

    @classmethod
    def load(cls, payload: bytes):
        data = Framer.decode(payload[4:])
        p = dict(zip(cls.__fields__, data[1:]))
        return cls(**p)


def discover():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        # Enable port reusage so we will be able to run multiple clients and servers on single (host, port).
        # Do not use socket.SO_REUSEADDR except you using linux(kernel<3.9): goto https://stackoverflow.com/questions/14388706/how-do-so-reuseaddr-and-so-reuseport-differ for more information.
        # For linux hosts all sockets that want to share the same address and port combination must belong to processes that share the same effective user ID!
        # So, on linux(kernel>=3.9) you have to run multiple servers and clients under one user to share the same (host, port).
        # Thanks to @stevenreddie
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Enable broadcasting mode
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        sock.bind(("255.255.255.255", 9943))
        data = None
        log.info("Start discover")
        while not data:
            data, client = sock.recvfrom(1024)
        payload = ClientHandshake.load(data)
        log.info(f"Find: {payload.hostname}")
        return payload.dict(), client
