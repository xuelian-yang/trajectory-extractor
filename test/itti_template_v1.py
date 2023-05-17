# -*- encoding: utf-8 -*-

# @File        :   itti_template_v1.py
# @Description :   
# @Time        :   2023/05/17 10:58:26
# @Author      :   Xuelian.Yang
# @Contact     :   Xuelian.Yang@geely.com
# @LastEditors :   Xuelian.Yang

# here put the import lib

import argparse
import os.path as osp
import sys

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '..')))
from common.util import get_name, itti_argparse, itti_debug, itti_main, itti_timer, save_json
from configs.workspace import WorkSpace


@itti_argparse
def get_parser():
    parser = argparse.ArgumentParser(
        description='Realtime mono tracking with trajectory-extractor')
    parser.add_argument('-v', '--video_path', type=str,
                        default='test_alaco/sample/W91_2023-04-25_17_23_31.mp4',
                        help='input video path')
    parser.add_argument('--output_dir', type=str,
                        default='',
                        help='Path of the output')
    parser.add_argument('--config_json', type=str,
                        default='',
                        help='Path to json config')
    args = parser.parse_args()
    return args


@itti_main
@itti_timer
@itti_debug
def main(py_file):
    args = get_parser()
    name = get_name(__file__)
    save_json(args, osp.join(WorkSpace().get_save_dir(__file__), f'{name}.json'))


if __name__ == '__main__':
    main(py_file=__file__)
