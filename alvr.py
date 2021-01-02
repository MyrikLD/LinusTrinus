#!/bin/python3
import logging

from callback.open_vr import OpenVR
from discover.alvr import discover
from frame_generator.xwd_fg import XwdFrameGenerator
from sensor_client.alvr import SensorClient

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main():
    hanshake, addr = discover()
    server_port = 9944

    client = SensorClient(addr, server_port=server_port, callback_objects=[OpenVR()])

    # Run frame generator for sender
    framegen = XwdFrameGenerator(client.msg_buf)

    framegen.start()
    client.start()

    framegen.join()
    client.join()


if __name__ == "__main__":
    main()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
