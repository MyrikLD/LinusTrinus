cdef extern from "rs.h":
    struct reed_solomon:
        pass

    void reed_solomon_init(void);
    reed_solomon*reed_solomon_new(int data_shards, int parity_shards);
    void reed_solomon_release(reed_solomon *rs);
    int reed_solomon_encode(reed_solomon *rs, unsigned char** shards, int nr_shards, int block_size);
    int reed_solomon_reconstruct(
            reed_solomon *rs, unsigned char** shards, unsigned char*marks, int nr_shards, int block_size
    );

def py_reed_solomon_init():
    return reed_solomon_init()

def py_reed_solomon_new(data_shards, parity_shards):
    return reed_solomon_new(data_shards, parity_shards)

def py_reed_solomon_release(rs):
    return reed_solomon_release(rs)

def py_reed_solomon_encode(rs, shards, nr_shards, block_size):
    return reed_solomon_encode(rs, shards, nr_shards, block_size)

def py_reed_solomon_reconstruct(rs, shards, marks, nr_shards, block_size):
    return reed_solomon_reconstruct(rs, shards, marks, nr_shards, block_size)
