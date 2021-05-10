#!/bin/python3

import logging
from time import sleep

from callback.open_vr import OpenVR
from discover import discover
from frame_generator.xwd_fg import XwdFrameGenerator
from sender import Sender
from sensor_client import SensorClient

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main():
    server_ip = discover()
    server_port = 4242 
    client_port = 7777

    sender = Sender(server_ip, server_port=server_port, client_port=client_port)

    # Run frame generator for sender
    framegen = XwdFrameGenerator(sender.settings, sender.framebuf)
    framegen.start()

    # Start sending frames to client
    sender.start()

    # Wait for sensor server init
    sleep(1)

    # TODO: doesnt connect to existing driver..
    client = SensorClient(
        server_ip, server_port=server_port, callback_objects=[OpenVR()]
    )
    client.start()

    client.join()
    sender.join()
    framegen.join()


if __name__ == "__main__":
    main()
