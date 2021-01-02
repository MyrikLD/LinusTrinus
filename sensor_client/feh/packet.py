from sensor_client.feh.rs import (
    py_reed_solomon_encode,
    py_reed_solomon_new,
    py_reed_solomon_release,
)

ALVR_MAX_PACKET_SIZE = 1400
ALVR_MAX_VIDEO_BUFFER_SIZE = ALVR_MAX_PACKET_SIZE - 100
ALVR_FEC_SHARDS_MAX = 20

m_fecPercentage = 10


def CalculateParityShards(data_shards: int, fec_percentage: int):
    total_parity_shards: int = (data_shards * fec_percentage + 99) // 100
    return total_parity_shards


def CalculateFECShardPackets(l: int, fec_percentage: int):
    max_data_shards: int = ((ALVR_FEC_SHARDS_MAX - 2) * 100 + 99 + fec_percentage) // (
        100 + fec_percentage
    )
    min_block_size: int = (l + max_data_shards - 1) // max_data_shards
    shard_packets: int = (
        min_block_size + ALVR_MAX_VIDEO_BUFFER_SIZE - 1
    ) // ALVR_MAX_VIDEO_BUFFER_SIZE

    return shard_packets


def FECSend(buf: bytes):
    l = len(buf)
    shard_packets = CalculateFECShardPackets(l, m_fecPercentage)
    block_size = shard_packets * ALVR_MAX_VIDEO_BUFFER_SIZE
    data_shards = (l + block_size - 1) // block_size
    total_parity_shards = CalculateParityShards(data_shards, m_fecPercentage)
    total_shards = data_shards + total_parity_shards

    rs = py_reed_solomon_new(data_shards, total_parity_shards)

    shards = [
        buf[i * block_size : i * block_size + block_size] for i in range(data_shards)
    ]

    if l % block_size != 0:
        shards[data_shards - 1] = buf[
            data_shards * block_size : data_shards * block_size + block_size
        ]

    ret = py_reed_solomon_encode(rs, shards, total_shards, block_size)
    py_reed_solomon_release(rs)

    return shards
