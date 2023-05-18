# -*- encoding: utf-8 -*-

# @File        :   itti_func.py
# @Time        :   2023/05/18 16:23:27
# @Author      :   Xuelian.Yang
# @Contact     :   Xuelian.Yang@
# @LastEditors :   Xuelian.Yang

# here put the import lib
import os.path as osp
import sys
sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '..')))
from common.util import itti_trackback

@itti_trackback
def create_2d_array():
    import numpy as np
    a = np.random.randint(5, size=(2, 3))
    return a

@itti_trackback
def get_time():
    import time
    return time.time()
