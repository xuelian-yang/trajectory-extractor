# -*- coding: utf-8 -*-

"""
将 run_visualizer.py 生成的图片导出为 gif

python util_create_gif.py -h
python util_create_gif.py --help

python util_create_gif.py

python util_create_gif.py ^
  --img_seq_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/visualizer/img_concat ^
  --gif_name alaco_traj_demo_alaco_W92_2023-05-09_14_18_54.gif
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
    frames = []
    images_dir = args.img_seq_dir
    if not osp.exists(images_dir):
        d_print_r(f'path not exist: {images_dir}')
        raise ValueError(f'path not exist: {images_dir}')
    logging.info(f'loading {images_dir}')

    files = sorted(glob.glob(f'{images_dir}/*.png'))

    for item in files:
        new_frame = Image.open(item)
        frames.append(new_frame)

    gif_name = osp.join(save_dir, args.gif_name)
    logging.info(f'saving {gif_name}')

    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif-saving
    frames[0].save(
        gif_name,
        format='GIF',
        append_images=frames[1:],
        save_all=True,  # all frames of the image will be saved.
        duration=150,  # The display duration of each frame of the multiframe gif, in milliseconds. 
        loop=0,  # Integer number of times the GIF should loop. 0 means that it will loop forever.
        comment=b'trajectory-extractor')


def main():
    argparser = argparse.ArgumentParser(
        description='image sequence to gif')
    argparser.add_argument('-c', '--img_seq_dir', type=str,
                           required=True,
                           help='image sequence path for loading')
    argparser.add_argument('-g', '--gif_name', type=str,
                           required=True,
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
