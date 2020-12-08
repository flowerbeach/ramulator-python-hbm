def calc_log2(val: int):
    n = 0
    val >>= 1
    while val > 0:
        n += 1
        val >>= 1
    return n


def slice_lower_bits(addr_int, bits):
    addr_low_bits = addr_int & ((1 << bits) - 1)
    addr_int >>= bits
    return addr_low_bits, addr_int


def clear_lower_bits(addr_int, bits):
    addr_int >>= bits
    return addr_int


if __name__ == '__main__':
    print(calc_log2(1))
