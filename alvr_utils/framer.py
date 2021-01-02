import struct


class Framer:
    @classmethod
    def decode(cls, payload: bytes, output=None, decode=True) -> list:
        if not payload:
            return output

        if not output:
            output = []

        # if not output:
        #     output = [struct.unpack("i", payload[:4])[0]]
        #     return cls.decode(payload[4:], output)
        # else:
        size = struct.unpack("Q", payload[:8])[0]

        if size == 0:
            output.append("")
            return cls.decode(payload[8:], output)

        body = struct.unpack(f"<{size}s", payload[8 : 8 + size])[0]
        output.append(body.decode() if decode else body)

        return cls.decode(payload[8 + size :], output)

    @staticmethod
    def encode(data: bytes) -> bytes:
        return struct.pack(f"Q", len(data)) + data
