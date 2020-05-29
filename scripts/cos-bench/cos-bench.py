# The functions to compare
import math
import configparser

def f1(degrees):
    return math.cos(degrees)


# Reporting
import time
import random

config = configparser.ConfigParser()
config.read('fileset/config')

count = int(config['cos-bench']['iterations'])
costime = 0

for i in range(count):  # adjust accordingly so whole thing takes a few sec
    t0 = time.time()
    f1(i)
    t1 = time.time()
    costime = costime + (t1 - t0)

print('math.cos ran', count , 'times in', costime, 'seconds')
