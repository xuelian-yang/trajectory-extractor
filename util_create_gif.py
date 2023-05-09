# -*- coding: utf-8 -*-

"""
将 run_visualizer.py 生成的图片导出为 gif
"""

import argparse
import copy
import csv
import cv2
from datetime import datetime
from distinctipy import distinctipy
import glob
import json
import logging
import math
from matplotlib import pyplot as plt
import numpy as np
import os
import os.path as osp
import pandas as pd
import PIL
import platform
import sys
from termcolor import colored
import time

from common.util import setup_log, d_print, get_name, d_print_b, d_print_g, d_print_r, d_print_y
from configs.workspace import WorkSpace

logger = logging.getLogger(__name__)
isWindows = (platform.system() == "Windows")

def images_to_gif(save_dir):
    data_dir = 'E:/Github/trajectory-extractor/test_alaco'
    case_dir = 'temp_v2_alaco_W92_2023-05-09_14_18_54/output/visualizer/img_sat_concat'

    gif_name = osp.join(save_dir, 'alaco_demo_trajectory-extractor.gif')
    frames = []
    images_dir = osp.join(data_dir, case_dir)
    if not osp.exists(images_dir):
        raise ValueError(f'path not exist: {images_dir}')

    files = sorted(glob.glob(f'{images_dir}/*.png'))
    # for idx, item in enumerate(files):
    #    print(f'{idx:4d} {item}')

    for item in files:
        new_frame = PIL.Image.open(item)
        frames.append(new_frame)
    frames[0].save(
        gif_name,
        format='GIF',
        append_images=frames[1:],
        save_all=True,
        duration=100,
        loop=0,
        comment=b'trajectory-extractor')

def main():
    argparser = argparse.ArgumentParser(
        description='generate feature point files for calibration')
    argparser.add_argument('--labelme_json', default='feature_points_10.10.145.231.json')
    args = argparser.parse_args()

    ws = WorkSpace()
    save_dir = osp.join(ws.get_temp_dir(), get_name(__file__))
    if not osp.exists(save_dir):
        os.makedirs(save_dir)

    images_to_gif(save_dir)


if __name__ == "__main__":
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    main()

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
