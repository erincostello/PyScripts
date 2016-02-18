
from __future__ import print_function
import filecmp

a = r"\\DEQWQNAS01\Lidar08\LiDAR\BE"
b = r"P:\Willamette\BE"

match, mismatch, err = filecmp.cmpfiles(a, b, common)

print(mismatch)