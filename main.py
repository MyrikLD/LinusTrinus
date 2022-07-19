#!/bin/python3
import logging
from time import sleep

from callback.open_vr import OpenVR
from constants import FRAMEGEN_DOUBLE
from constants import FRAMEGEN_FFMPEG
from constants import FRAMEGEN_SIMPLE
from constants import FRAMEGEN_XWD
from discover import discover
from frame_generator.ffmpeg_double_fg import FfmpegDoubleFrameGenerator
from frame_generator.ffmpeg_fg import FfmpegFrameGenerator
from frame_generator.xwd_fg import XwdFrameGenerator
from sender import Sender
from sensor_client import SensorClient

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main():
    server_ip = discover()
    server_port = 5555
    client_port = 7777
    framegen_type = FRAMEGEN_FFMPEG
    framegen_video_type = FRAMEGEN_DOUBLE
    sender = Sender(server_ip, server_port=server_port, client_port=client_port)

    # Run frame generator for sender
    framegen = None
    if framegen_type == FRAMEGEN_FFMPEG:
        if framegen_video_type == FRAMEGEN_DOUBLE:
            framegen = FfmpegDoubleFrameGenerator(sender.settings, sender.framebuf)
        if framegen_video_type == FRAMEGEN_SIMPLE:
            framegen = FfmpegFrameGenerator(sender.settings, sender.framebuf)
    if framegen_type == FRAMEGEN_XWD:
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
