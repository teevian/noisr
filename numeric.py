import statistics

def statistic(self, bitword):
    """
        Returns a dictionary with basic statistics about the generated number
    """
    bit_string = ''.join(str(bit) for bit in self.wordbit)
    size = len(bitword)
    decimal = int(bit_string, 2)
    n_ones = sum(self.wordbit)
    n_zeroes = self.bitsize - n_ones

    return {
        'n_bits': size,
        'n_ones' : n_ones,
        'n_zeroes': n_zeroes,
        'ratio_1t0': float(n_ones) / size * 100,
        'bin': bit_string,
        'dec': decimal
    }

def binary_tests(bin_num):
    