import struct
import numpy as np
from typing import List, Tuple

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

class MovingAverage:
    def __init__(self, data, window_size):
        self.arr = data
        self.window_size = window_size

    @staticmethod
    def simple(arr, window_size):
        weights = np.ones(window_size) / window_size
        return np.convolve(arr, weights, mode='valid')

    @staticmethod
    def cumulative(arr, window_size):
        weights = np.cumsum(np.ones(window_size)) / window_size
        weights[window_size:] = weights[window_size:] - weights[:-window_size]
        return np.convolve(arr, weights, mode='valid')

    @staticmethod
    def weighted(arr, window_size):
        weights = np.arange(1, window_size+1)
        weights = weights / np.sum(weights)
        return np.convolve(arr, weights, mode='valid')

    @staticmethod
    def exponential(arr, window_size):
        weights = np.exp(np.linspace(-1., 0., window_size))
        weights = weights / np.sum(weights)
        return np.convolve(arr, weights, mode='valid')

    @staticmethod
    def triangular(arr, window_size):
        weights = np.arange(1, window_size+1)
        weights = 2 * weights / (window_size * (window_size + 1))
        return np.convolve(arr, weights, mode='valid')

    @staticmethod
    def bartlett(arr, window_size):
        weights = np.arange(1, window_size+1)
        weights = 2 * weights / (window_size - 1)
        weights[0] /= 2
        weights[-1] /= 2
        return np.convolve(arr, weights, mode='valid')

    def __call__(self, method='simple'):
        return getattr(MovingAverage, method)(self.arr, self.window_size)


def movingAverage(arr, window_size, method='simple'):
    moving_average = MovingAverage(arr, window_size)
    return moving_average(method)

def calculate_fft(data: List[Tuple[float, float]]) -> Tuple[np.ndarray, np.ndarray]:
    """
        Calculates the FFT of a list of pairs where the first element is time and the second element is voltage

        Args:
            data: A list of pairs where the first element is time and the second element is voltage

        Returns:
            A tuple containing the frequency bins and FFT values
    """
    times, voltages = np.array(data).T
    
    # Calculate the sample rate and number of samples
    sample_rate = 1 / np.mean(np.diff(times))
    n_samples = len(voltages)

    # Calculate the frequency bins and perform the FFT
    frequency_bins = np.fft.rfftfreq(n_samples, d=1/sample_rate)
    fft_values = np.fft.rfft(voltages)
    
    # Return the frequency bins and FFT values as a tuple
    return frequency_bins, fft_values