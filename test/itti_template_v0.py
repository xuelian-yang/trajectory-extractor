# -*- encoding: utf-8 -*-

# @File        :   itti_template_v0.py
# @Description :   
# @Time        :   2023/05/17 09:43:08
# @Author      :   Xuelian.Yang
# @Contact     :   Xuelian.Yang@
# @LastEditors :   Xuelian.Yang
# @Example     :   python test/itti_template_v0.py

# here put the import lib

import argparse
import logging
import json
import os
import os.path as osp
import platform
import sys
from termcolor import colored
import time

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '..')))
from common.util import setup_log, get_name, itti_debug, itti_timer, Profile
from configs.workspace import WorkSpace

logger = logging.getLogger(__name__)
isWindows = (platform.system() == "Windows")


@itti_timer
@itti_debug
def run_xxx(config):
    # Create output folder
    output_dir = config.output_dir
    output_dir = osp.join(output_dir, 'xxx')
    os.makedirs(output_dir, exist_ok=True)

    # Save the cfg file with the output:
    try:
        cfg_save_path = osp.join(output_dir, 'xxx_cfg.json')
        with open(cfg_save_path, 'w') as json_file:
            config_dict = vars(config)
            json.dump(config_dict, json_file, indent=4)
    except Exception as e:
        print('[ERROR]: Error saving config file in output folder:\n')
        print('{}'.format(e))
        return False


@itti_timer
@itti_debug
def main():
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
    if osp.isfile(args.config_json):
        with open(args.config_json, 'r') as f:
            data_json = json.load(f)
            vars(args).update(data_json)
    vars(args).pop('config_json', None)
    logger.warning(f'argparse.ArgumentParser:')

    args = parser.parse_args()
    logger.warning(f'argparse.ArgumentParser:')
    char_concat = '^' if isWindows else '\\'
    __text = f'\npython {osp.basename(__file__)} {char_concat}\n'
    for item in vars(args):
        __text += f'  -{item} {getattr(args, item)} {char_concat}\n'
        logger.info(f'{item:20s} : {getattr(args, item)}')
    logger.info(f'{__text}')

    ws = WorkSpace()
    save_dir = osp.join(ws.get_temp_dir(), get_name(__file__))
    if not osp.exists(save_dir):
        os.makedirs(save_dir)

    if args.output_dir == '':
        args.output_dir = save_dir

    run_xxx(args)


if __name__ == '__main__':
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    main()

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
