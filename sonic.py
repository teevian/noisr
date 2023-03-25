import struct 

def Q_rsqrt(number: float):
    threehalfs = 1.5
    x2 = number * 0.5
    y = number
    packed_y = struct.pack('f', y)
    i = struct.unpack('i', packed_y)[0]     # evil floating point bit level hacking
    i = 0x5f3759df - (i >> 1)               # what the ****?
    packed_i = struct.pack('i', i)
    y = struct.unpack('f', packed_i)[0]
    y = y * (threehalfs - (x2 * y * y))     # 1st iteration
#   y = y * (threehalfs - (x2 * y * y))     # 2nd iteration, this can be removed

    return y
