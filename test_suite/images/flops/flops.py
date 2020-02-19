"""
Flop test for Abaco. Reads in a string message of "'threads' 'std_deviation' 'size'" from
Abaco. Does some cool multi-threaded math and outputs total time to completion.
"""
import os
import time

threads, std_dev, size, iterations = map(int, os.environ.get('MSG').split())

if threads:
    os.environ["OMP_NUM_THREADS"] = str(threads)

import numpy
whole_start = time.time()
A = numpy.random.normal(0, std_dev, (size, size))
B = numpy.random.normal(0, std_dev, (size, size))

calc_start = time.time()
for _ in range(iterations):
    numpy.dot(A, B)

end = time.time()

print(end - whole_start, end - calc_start)
