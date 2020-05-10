import socket
from logging import getLogger

log = getLogger(__name__)


def discover():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 7777))
    data = None
    log.info("Start discover")
    while not data or data[0] != b"e":
        data = sock.recvfrom(1)
    if data[0] == b"e":
        log.info("Find: %s" % data[1][0])
        return data[1][0]
    sock.close()
