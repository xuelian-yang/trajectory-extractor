# -*- coding: utf-8 -*-

###################################################################################
#
# Script that opens a video and save the frames individually with their timestamps
#
###################################################################################

import cv2
import numpy as np
import platform
import time
import copy
import os
import csv
import argparse

import logging
import os.path as osp
import sys
from termcolor import colored
sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '../..')))
from common.util import setup_log, d_print, get_name, d_print_b, d_print_g, d_print_r, d_print_y
from configs.workspace import WorkSpace

logger = logging.getLogger(__name__)
isWindows = (platform.system() == "Windows")

def main():

    ##########################################################
    # Cmd Line program
    ##########################################################

    parser = argparse.ArgumentParser(description='Split video into timestamped images. Name are "videoname_XXXXXX.jpg" with XXXXX timestamp in ms.');
    parser.add_argument(dest="video_path", type=str, help='path of the video_file' );
    parser.add_argument('-o', dest="output_folder", type=str, help='path of the output folder' );
    parser.add_argument('-c', dest="crop", nargs = '*', type=int, help='Cropping values: x1 y1 x2 y2' );
    parser.add_argument('-t', dest="time_max_s",  type=int, help='Stop extracting images after this time in seconds');
    parser.add_argument('--skip', default=1,  type=int, help='Save one frame every skip frame' );
    parser.add_argument('--max_frame_num', default=500, type=int, help='Only parse first max_frame_num frames')
    parser.add_argument('--frame_start', default=0, type=int, help='skip first frame_start frames')
    args = parser.parse_args()
    logger.warning(f'argparse.ArgumentParser:')
    char_concat = '^' if isWindows else '\\'
    __text = f'\npython {osp.basename(__file__)} {char_concat}\n'
    for item in vars(args):
        __text += f'  -{item} {getattr(args, item)} {char_concat}\n'
        logger.info(f'{item:20s} : {getattr(args, item)}')
    logger.info(f'{__text}')

    ##########################################################
    # Crop mode
    ##########################################################
    crop_mode = False;
    if not (args.crop is None):
        crop_mode = True;

        if len(args.crop) != 4:
            print('[ERROR]: crop option needs 4 arguments, but {} given'.format(len(args.crop)));
            return;

        crop_x1y1x2y2 = args.crop;

    ##########################################################
    # Open Video
    ##########################################################

    # Init the video reader
    capture = cv2.VideoCapture(args.video_path)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    ##########################################################
    # Open Output files
    ##########################################################

    # Get name of the video
    video_name = args.video_path.split('/')[-1];
    video_name = video_name.split('.')[0];

    # If outpath is not specified, svae images in the output folder
    if args.output_folder is None:

        # Get folder of the video
        output_path = os.path.dirname(os.path.abspath(args.video_path));

    else:
        output_path = args.output_folder;

    output_path_img = output_path + '/img'
    os.makedirs(output_path_img, exist_ok=True)

    print('Saving frames:{} '.format(output_path_img))

    ##########################################################
    # Run through the video
    ##########################################################

    # Record frame number
    frame_number = 0;

    ret = True;
    while ret:

        #Get time
        stime = time.time()
        time_ms = int(capture.get(cv2.CAP_PROP_POS_MSEC));
        time_ms_str = str(time_ms).zfill(10);

        # Check time:
        if not (args.time_max_s is None):
            if time_ms > args.time_max_s*1000:
                print('Maximum time reached: time: {}s > time_max: {}s'.format(time_ms/1000, args.time_max_s));
                break;

        ret, frame = capture.read()

        # Crop if crop mode
        if crop_mode:
            frame = frame[crop_x1y1x2y2[1]:crop_x1y1x2y2[3], crop_x1y1x2y2[0]:crop_x1y1x2y2[2], :];

        # Save video
        current_name = video_name + '_' + time_ms_str;
        name_image = current_name + '.jpg';

        frame_number = frame_number + 1
        if frame_number > args.max_frame_num:
            break

        if frame_number < args.frame_start:
            continue

        # if save:

        if frame_number%args.skip == 0 and frame is not None:
            cv2.imwrite( output_path_img + '/' + name_image, frame );
            print('Frame Number: {} {}'.format(frame_number, name_image))

    print('\n**** Job is done ****\n{} frames saved at {}\n'.format(frame_number, output_path_img))

    capture.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    ws = WorkSpace()
    save_dir = osp.join(ws.get_temp_dir(), get_name(__file__))
    if not osp.exists(save_dir):
        os.makedirs(save_dir)

    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
