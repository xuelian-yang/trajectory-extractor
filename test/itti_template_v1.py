# -*- encoding: utf-8 -*-

# @File        :   itti_template_v1.py
# @Description :   
# @Time        :   2023/05/17 10:58:26
# @Author      :   Xuelian.Yang
# @Contact     :   Xuelian.Yang@
# @LastEditors :   Xuelian.Yang
# @Example     :   python test/itti_template_v1.py

# here put the import lib

import argparse
import os.path as osp
import sys

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '..')))
from common.util import get_name, itti_argparse, itti_debug, itti_main, itti_timer, itti_traceback, save_json
from configs.workspace import WorkSpace

sys.path.append(osp.dirname(__file__))
from itti_func import create_2d_array, get_time

@itti_traceback
@itti_argparse
def get_parser():
    parser = argparse.ArgumentParser(
        description='Realtime mono tracking with trajectory-extractor')
    parser.add_argument('--py_file', type=str, default=__file__,
                        help='name of python file')
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


@itti_traceback
def run_xxx(args):
    create_2d_array()
    get_time()


@itti_traceback
@itti_main
@itti_timer
@itti_debug
def main(py_file):
    args = get_parser()
    name = get_name(__file__)
    save_dir = WorkSpace().get_save_dir(__file__)
    save_json(args, osp.join(save_dir, f'{name}_cfg.json'))
    if args.output_dir == '':
        args.output_dir = save_dir

    for _ in range(10):
        run_xxx(args)

if __name__ == '__main__':
    main(py_file=__file__)
