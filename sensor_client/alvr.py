import logging
import os
import socket
from datetime import datetime
from threading import Thread
from typing import Tuple

import pyximport

from alvr_utils.client_config_packet import ClientConfigPacket
from alvr_utils.packet import VideoFrame, parse_packet
from drop_queue import DropQueue

pyximport.install(setup_args={'include_dirs': os.path.abspath(".")})
from sensor_client.feh.rs import FECSend


class Ip:
    body: str

    def __init__(self, ip):
        self.body = ip

    @classmethod
    def load(cls, data: bytes):
        ip = ".".join(str(i) for i in data[-4:])
        return cls(ip)

    def dump(self):
        return bytes([int(i) for i in self.body.split(".")])

    def __str__(self):
        return self.body

    __repr__ = __str__


log = logging.getLogger(__name__)
config = {
    "setupWizard": False,
    "openvrConfig": {
        "universe_id": 2,
        "headset_serial_number": "1WMGH000XX0000",
        "headset_tracking_system_name": "oculus",
        "headset_model_number": "Oculus Rift S",
        "headset_driver_version": "1.42.0",
        "headset_manufacturer_name": "Oculus",
        "headset_render_model_name": "generic_hmd",
        "headset_registered_device_type": "oculus/1WMGH000XX0000",
        "eye_resolution_width": 1344,
        "eye_resolution_height": 1440,
        "target_eye_resolution_width": 1344,
        "target_eye_resolution_height": 1440,
        "enable_game_audio": True,
        "game_audio_device": "{0.0.0.00000000}.{76074a87-23b0-49f9-a133-bdf086b63661}",
        "mute_host_audio_output": True,
        "enable_microphone": False,
        "microphone_device": "{0.0.0.00000000}.{1ff6723b-05ff-4811-8650-4f21ea35c4f9}",
        "seconds_from_vsync_to_photons": 0.005,
        "ipd": 0.063,
        "client_buffer_size": 60000,
        "force_3dof": False,
        "aggressive_keyframe_resend": False,
        "adapter_index": 0,
        "codec": 0,
        "refresh_rate": 60,
        "encode_bitrate_mbs": 15,
        "throttling_bitrate_bits": 47000000,
        "listen_port": 9944,
        "client_address": "192.168.18.126",
        "controllers_tracking_system_name": "oculus",
        "controllers_manufacturer_name": "Oculus",
        "controllers_model_number": "Oculus Rift S",
        "render_model_name_left_controller": "oculus_rifts_controller_left",
        "render_model_name_right_controller": "oculus_rifts_controller_right",
        "controllers_serial_number": "1WMGH000XX0000_Controller",
        "controllers_type": "oculus_touch",
        "controllers_registered_device_type": "oculus/1WMGH000XX0000_Controller",
        "controllers_input_profile_path": "{oculus}/input/touch_profile.json",
        "controllers_mode_idx": 1,
        "controllers_enabled": True,
        "position_offset": [0.0, 0.0, 0.0],
        "tracking_frame_offset": 0,
        "controller_pose_offset": -1.0,
        "position_offset_left": [-0.007, 0.005, -0.053],
        "rotation_offset_left": [36.0, 0.0, 0.0],
        "haptics_intensity": 1.0,
        "enable_foveated_rendering": True,
        "foveation_strength": 2.0,
        "foveation_shape": 1.5,
        "foveation_vertical_offset": 0.0,
        "enable_color_correction": False,
        "brightness": 0.0,
        "contrast": 0.0,
        "saturation": 0.0,
        "gamma": 1.0,
        "sharpening": 0.0,
    },
    "clientConnections": {
        "16605.client.alvr": {
            "deviceName": "Oculus Quest 2",
            "lastLocalIp": "192.168.18.126",
            "manualIps": [],
            "trusted": True,
            "certificatePem": "-----BEGIN CERTIFICATE-----\r\nMIIBUTCB+aADAgECAgEqMAoGCCqGSM49BAMCMCExHzAdBgNVBAMMFnJjZ2VuIHNl\r\nbGYgc2lnbmVkIGNlcnQwIBcNNzUwMTAxMDAwMDAwWhgPNDA5NjAxMDEwMDAwMDBa\r\nMCExHzAdBgNVBAMMFnJjZ2VuIHNlbGYgc2lnbmVkIGNlcnQwWTATBgcqhkjOPQIB\r\nBggqhkjOPQMBBwNCAAQY82sCH/5LZHJtNT8z6LRGIff6ViRcrLwGv8/0xsKg9IY4\r\nVARYZQrBiNnVHjcNFYp98X+4uShRvAQaM8Ef+2CUoyAwHjAcBgNVHREEFTATghEx\r\nNjYwNS5jbGllbnQuYWx2cjAKBggqhkjOPQQDAgNHADBEAiAkptMib0oOvmN7l0ec\r\nKUZS4wYA3yH4DCldftMZefloeQIgH0p0ACEz3bJyEkWVxAaKeVDycPOxvyi8Tw/L\r\njjr+Tg0=\r\n-----END CERTIFICATE-----\r\n",
        }
    },
    "sessionSettings": {
        "video": {
            "adapterIndex": 0,
            "preferredFps": 60.0,
            "renderResolution": {
                "scale": 0.75,
                "absolute": {"width": 2880, "height": 1600},
                "variant": "scale",
            },
            "recommendedTargetResolution": {
                "scale": 0.75,
                "absolute": {"width": 2880, "height": 1600},
                "variant": "scale",
            },
            "secondsFromVsyncToPhotons": 0.005,
            "ipd": 0.063,
            "foveatedRendering": {
                "enabled": True,
                "content": {"strength": 2.0, "shape": 1.5, "verticalOffset": 0.0},
            },
            "colorCorrection": {
                "enabled": False,
                "content": {
                    "brightness": 0.0,
                    "contrast": 0.0,
                    "saturation": 0.0,
                    "gamma": 1.0,
                    "sharpening": 0.0,
                },
            },
            "codec": {"variant": "HEVC"},
            "clientRequestRealtimeDecoder": True,
            "encodeBitrateMbs": 15,
        },
        "audio": {
            "gameAudio": {
                "enabled": True,
                "content": {
                    "device": "{0.0.0.00000000}.{76074a87-23b0-49f9-a133-bdf086b63661}",
                    "muteWhenStreaming": True,
                },
            },
            "microphone": {
                "enabled": False,
                "content": {
                    "device": "{0.0.0.00000000}.{1ff6723b-05ff-4811-8650-4f21ea35c4f9}"
                },
            },
        },
        "headset": {
            "universeId": 2,
            "serialNumber": "1WMGH000XX0000",
            "trackingSystemName": "oculus",
            "modelNumber": "Oculus Rift S",
            "driverVersion": "1.42.0",
            "manufacturerName": "Oculus",
            "renderModelName": "generic_hmd",
            "registeredDeviceType": "oculus/1WMGH000XX0000",
            "trackingFrameOffset": 0,
            "positionOffset": [0.0, 0.0, 0.0],
            "force3dof": False,
            "controllers": {
                "enabled": True,
                "content": {
                    "modeIdx": 1,
                    "trackingSystemName": "oculus",
                    "manufacturerName": "Oculus",
                    "modelNumber": "Oculus Rift S",
                    "renderModelNameLeft": "oculus_rifts_controller_left",
                    "renderModelNameRight": "oculus_rifts_controller_right",
                    "serialNumber": "1WMGH000XX0000_Controller",
                    "ctrlType": "oculus_touch",
                    "registeredDeviceType": "oculus/1WMGH000XX0000_Controller",
                    "inputProfilePath": "{oculus}/input/touch_profile.json",
                    "poseTimeOffset": -1.0,
                    "clientsidePrediction": False,
                    "positionOffsetLeft": [-0.007, 0.005, -0.053],
                    "rotationOffsetLeft": [36.0, 0.0, 0.0],
                    "hapticsIntensity": 1.0,
                },
            },
            "trackingSpace": {"variant": "local"},
        },
        "connection": {
            "autoTrustClients": False,
            "webServerPort": 8082,
            "listenPort": 9944,
            "throttlingBitrateBits": 47000000,
            "clientRecvBufferSize": 60000,
            "aggressiveKeyframeResend": False,
        },
        "extra": {
            "theme": {"variant": "systemDefault"},
            "revertConfirmDialog": True,
            "restartConfirmDialog": False,
            "promptBeforeUpdate": True,
            "updateChannel": {"variant": "stable"},
            "logToDisk": False,
            "notificationLevel": {"variant": "warning"},
            "excludeNotificationsWithoutId": False,
        },
    },
}


class SensorClient(Thread):
    buffer_size = 1514
    data = None

    def __init__(self, client: Tuple[str, int], server_port=9944, callback_objects=()):
        Thread.__init__(self)
        self.packetCounter = 0
        self.videoPacketCounter = 0

        connection = {
            "autoTrustClients": False,
            "webServerPort": 8082,
            "listenPort": server_port,
            "throttlingBitrateBits": 47000000,
            "clientRecvBufferSize": 60000,
            "aggressiveKeyframeResend": False,
        }
        config["sessionSettings"]["connection"] = connection

        # self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.bind(("", connection["listenPort"]))
        # self.listen(1)
        self.client = client
        self.msg_buf = DropQueue(2)
        self.callback = [i.callback for i in callback_objects]

    def run(self):
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp.bind(("", config["sessionSettings"]["connection"]["listenPort"]))

        self.tcp = self.ask_connection(self.client)

        while 1:
            self.handle_read()
            # self.handle_write()

    def ask_connection(self, client):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(client)

        init_data = sock.recv(self.buffer_size)
        my_ip = Ip.load(init_data[-4:])

        port = config["sessionSettings"]["connection"]["webServerPort"]
        config_packet = ClientConfigPacket(
            session_desc=config,
            eye_resolution_width=1344,
            eye_resolution_height=1440,
            fps=60,
            web_gui_url=f"http://{my_ip}:{port}/",
        )
        sock.send(config_packet.pack())
        return sock

    @staticmethod
    def timestamp():
        return int(datetime.now().timestamp() * 1000000)

    def handle_read(self):
        data, address = self.udp.recvfrom(self.buffer_size)
        if data:
            self.on_data(data)

            if not self.msg_buf.empty():
                image = self.msg_buf.get()
                fec_percentage = 5
                result = FECSend(image, len(image), fec_percentage)

                vf = VideoFrame(
                    packetCounter=self.packetCounter,
                    trackingFrameIndex=1,
                    videoFrameIndex=1,
                    sentTime=self.timestamp(),
                    frameByteSize=len(image),
                    fecIndex=0,
                    fecPercentage=fec_percentage,
                )

                ALVR_MAX_PACKET_SIZE = 1400
                ALVR_MAX_VIDEO_BUFFER_SIZE = ALVR_MAX_PACKET_SIZE - len(vf.pack())
                dataRemain = len(image)
                for i in range(result.dataShards):
                    for j in range(result.shardPackets):
                        copyLength = min(ALVR_MAX_VIDEO_BUFFER_SIZE, dataRemain)
                        if copyLength <= 0:
                            break
                        p = j * ALVR_MAX_VIDEO_BUFFER_SIZE
                        payload = result.shards[i][p: p + copyLength]
                        dataRemain -= ALVR_MAX_VIDEO_BUFFER_SIZE
                        vf.packetCounter = self.videoPacketCounter
                        self.videoPacketCounter += 1
                        vf.sentTime = self.timestamp()
                        self.udp.sendto(vf.pack() + payload, address)
                        vf.fecIndex += 1

                vf.fecIndex = result.dataShards * result.shardPackets

                for i in range(result.totalParityShards):
                    for j in range(result.shardPackets):
                        copyLength = ALVR_MAX_VIDEO_BUFFER_SIZE
                        p = j * ALVR_MAX_VIDEO_BUFFER_SIZE
                        payload = result.shards[result.dataShards + i][p:copyLength]
                        vf.packetCounter = self.videoPacketCounter
                        self.videoPacketCounter += 1
                        vf.sentTime = self.timestamp()
                        self.udp.sendto(vf.pack() + payload, address)
                        vf.fecIndex += 1

    def decode_pos(self, data):
        d = parse_packet(data)
        return d

    def on_data(self, data):
        if not data:
            return
        self.data = self.decode_pos(data)

        if self.data:
            for callback in self.callback:
                try:
                    callback(self.data)
                except Exception as e:
                    log.exception(e)
