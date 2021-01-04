cdef extern from "sensor_client/feh/rs.c":
    ctypedef struct run_result:
        unsigned int totalShards;
        unsigned int blockSize;
        unsigned int shardPackets;
        unsigned int dataShards;
        unsigned int totalParityShards;
        unsigned char** shards;

    run_result*run(unsigned char *buf, unsigned int len, unsigned int m_fecPercentage)

cdef convert_to_python(unsigned char ** ptr, int n, int size):
    cdef int i
    lst = []
    for i in range(n):
        d = b''
        for j in range(size):
            d += bytes([ptr[i][j]])
        lst.append(d)
    return lst


class FECSend:
    def __init__(self, buf, lenbuf, m_fecPercentage):
        cdef run_result *r;
        r = run(buf, lenbuf, m_fecPercentage)
        self.shards = convert_to_python(r.shards, r.totalShards, r.blockSize)
        self.totalShards = r.totalShards
        self.blockSize = r.blockSize
        self.shardPackets = r.shardPackets
        self.dataShards = r.dataShards
        self.totalParityShards = r.totalParityShards


def py_run(buf, lenbuf, m_fecPercentage):
    return FECSend(buf, lenbuf, m_fecPercentage)
