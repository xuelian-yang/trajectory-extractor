# -*- coding: utf-8 -*-

"""
将 run_visualizer.py 生成的图片导出为 gif

python util_create_gif.py -h
python util_create_gif.py --help

python util_create_gif.py

python util_create_gif.py ^
  --case_name temp_v2_alaco_W92_2023-05-09_14_18_54 ^
  --gif_name alaco_demo_trajectory-extractor_partial.gif
"""

import argparse
import glob
import logging
import os
import os.path as osp
from PIL import Image
import platform
from termcolor import colored
import time

from common.util import setup_log, d_print, get_name, d_print_b, d_print_g, d_print_r, d_print_y
from configs.workspace import WorkSpace

logger = logging.getLogger(__name__)
isWindows = (platform.system() == "Windows")


def images_to_gif(args, save_dir):
    path_prefix = 'E:/Github/trajectory-extractor/test_alaco'
    path_suffix = 'output/visualizer/img_sat_concat'

    frames = []
    images_dir = osp.join(path_prefix, args.case_name, path_suffix)
    if not osp.exists(images_dir):
        raise ValueError(f'path not exist: {images_dir}')
    d_print_b(f'loading {images_dir}')

    files = sorted(glob.glob(f'{images_dir}/*.png'))

    for item in files:
        new_frame = Image.open(item)
        frames.append(new_frame)

    gif_name = osp.join(save_dir, args.gif_name)
    d_print_b(f'saving {gif_name}')
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
        description='image sequence to gif')
    argparser.add_argument('-c', '--case_name', type=str,
                           default='alaco_W92_2023-05-09_14_18_54',
                           help='case name for loading')
    argparser.add_argument('-g', '--gif_name', type=str,
                           default='alaco_demo_trajectory-extractor.gif',
                           help='gif name for saving')
    args = argparser.parse_args()
    for item in vars(args):
        logger.info(f'{item:20s} : {getattr(args, item)}')

    ws = WorkSpace()
    save_dir = osp.join(ws.get_temp_dir(), get_name(__file__))
    if not osp.exists(save_dir):
        os.makedirs(save_dir)

    images_to_gif(args, save_dir)


if __name__ == "__main__":
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    main()

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
