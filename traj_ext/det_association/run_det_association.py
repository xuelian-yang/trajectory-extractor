# -*- coding: utf-8 -*-

"""
对 run_detections_csv.py 生成的单帧结果进行匹配跟踪.

python traj_ext/det_association/run_det_association.py ^
  -image_dir test_alaco/alaco_W92_2023-05-09_14_18_54/img ^
  -output_dir  test_alaco/alaco_W92_2023-05-09_14_18_54/output/vehicles ^
  -det_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/det/csv ^
  -ignore_detection_area test_alaco/alaco_W92_2023-05-09_14_18_54/ ^
  -det_zone_im test_alaco/alaco_W92_2023-05-09_14_18_54/10.10.145.232_detection_zone_im.yml ^
  -mode vehicles ^
  -no_save_images
"""

##########################################################################################
#
# MEASUREMENT ASSOCIATION TO FORM TRACKS
#
# Association is done based on Intersection-Over-Union between masks of successive frames
#
##########################################################################################

import os
import sys

import random
import math
import numpy as np
import platform
import time
import json

import csv
import configparser
import argparse
from shutil import copyfile
import pickle

import cv2
import matplotlib
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
import pandas as pd

import sys
import os.path as osp
sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '../..')))

from traj_ext.det_association import multiple_overlap_association
from traj_ext.det_association.track_merge import TrackMerge
from traj_ext.det_association import track_2D

from traj_ext.object_det.det_object import DetObject
from traj_ext.object_det import det_object as det_object_file

from traj_ext.postprocess_track import trajutil

from traj_ext.utils import det_zone
from traj_ext.utils import cfgutil

import logging
import os.path as osp
import sys
from termcolor import colored
from common.util import setup_log, d_print, get_name, d_print_b, d_print_g, d_print_r, d_print_y, itti_timer, Profile
from configs.workspace import WorkSpace

logger = logging.getLogger(__name__)
isWindows = (platform.system() == "Windows")

label_list_vehicle = ['car','bus','truck', 'motorcycle'];
label_list_person = ['person', 'bicycle'];

def main(args_input):

    # Print instructions
    print("############################################################")
    print("Measurement Association based on Intersection-Over-Union")
    print("############################################################\n")

    # ##########################################################
    # # Parse Arguments
    # ##########################################################
    argparser = argparse.ArgumentParser(
        description='Measurement Association based on Intersection-Over-Union')
    argparser.add_argument(
        '-image_dir',
        default='',
        help='Path of the image folder')
    argparser.add_argument(
        '-det_dir',
        default='',
        help='Path of the detection folder');
    argparser.add_argument(
        '-det_zone_im',
        default='',
        help='Path of the detection zone im file');
    argparser.add_argument(
        '-ignore_detection_area',
        default='',
        help='Path of ignore detection area file');

    argparser.add_argument(
        '-output_dir',
        default='',
        help='Path of the output');

    argparser.add_argument(
        '-no_save_csv',
        action ='store_true',
        help='Do not save output as csv');
    argparser.add_argument(
        '-no_save_images',
        action ='store_true',
        help='Do not save output images');
    argparser.add_argument(
        '-show_images',
        action ='store_true',
        help='Show detections on images');
    argparser.add_argument(
        '-associate_with_label',
        action ='store_true',
        help='Successive detections must have same labels');
    argparser.add_argument(
        '-threshold_overlap',
        type =float,
        default=0.3,
        help='Minimum overlap between masks');
    argparser.add_argument(
        '-nb_frame_past',
        type =int,
        default=10,
        help='Number of past frame considered');
    argparser.add_argument(
        '-delete_det_out_det_zone',
        action ='store_true',
        help='Delete detection outside the detection zone');
    argparser.add_argument(
        '-shrink_zone',
        type=float,
        default =1.0,
        help='Shrink factor for detection zone');
    argparser.add_argument(
        '-mode',
        type=str,
        default ='vehicles',
        help='Mode: \'vehicles\' or \'pedestrians\'');

    argparser.add_argument(
        '-config_json',
        default='',
        help='Path to json config')
    argparser.add_argument(
        '-frame_limit',
        type=int,
        default=0,
        help='Frame limit: 0 = no limit')

    args = argparser.parse_args(args_input);

    if os.path.isfile(args.config_json):
        with open(args.config_json, 'r') as f:
            data_json = json.load(f)
            vars(args).update(data_json)

    vars(args).pop('config_json', None);
    logger.warning(f'argparse.ArgumentParser:')
    char_concat = '^' if isWindows else '\\'
    __text = f'\npython {osp.basename(__file__)} {char_concat}\n'
    for item in vars(args):
        __text += f'  -{item} {getattr(args, item)} {char_concat}\n'
        logger.info(f'{item:20s} : {getattr(args, item)}')
    logger.info(f'{__text}')

    return run_det_association(args);


@itti_timer
def run_det_association(config):
    __time_beg = time.time()
    # Create output folder
    output_dir = config.output_dir;
    output_dir = os.path.join(output_dir, 'det_association');
    os.makedirs(output_dir, exist_ok=True)

    # Save the cfg file with the output:
    try:
        cfg_save_path = os.path.join(output_dir, 'det_association_cfg.json');
        with open(cfg_save_path, 'w') as json_file:
            config_dict = vars(config);
            json.dump(config_dict, json_file, indent=4)
    except Exception as e:
        print('[ERROR]: Error saving config file in output folder:\n')
        print('{}'.format(e))
        return False;

    # Create output dorectory to save filtered image:
    overlap_img_dir = os.path.join(output_dir, 'img');
    os.makedirs(overlap_img_dir, exist_ok=True)
    overlap_csv_dir = os.path.join(output_dir, 'csv');
    os.makedirs(overlap_csv_dir, exist_ok=True)

    # Option for output
    delete_det_out_det_zone = config.delete_det_out_det_zone;
    save_csv = not config.no_save_csv;
    save_images = not config.no_save_images;
    show_images = config.show_images
    frame_limit = config.frame_limit;

    # Get mode:
    mode = config.mode;
    if mode == 'vehicles':
        label_list = label_list_vehicle;
    elif mode == 'pedestrians':
        label_list = label_list_person;
    else:
        print('[ERROR]: mode {} in config file not recognized, should be \'vehicles\' or \'pedestrians\'\n'.format(mode))
        return False;

    print('Det Association mode: {}\n'.format(mode))

    # Associate with label
    associate_with_label = config.associate_with_label;

    # Threshold to associate measurement: Need to overlap by at least this threshold
    threshold_overlap = config.threshold_overlap;

    # Number of frame we look into the past to associate measurement to a track
    nb_frame_past = config.nb_frame_past;

    # Print options
    print("Options: SHOW_IMAGES: {}, SAVE_IMAGES: {}, SAVE_CSV: {}".format(show_images, save_images, save_csv));

    # Load images
    img_folder_path = config.image_dir;
    list_img_file = os.listdir(img_folder_path);
    list_img_file.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))

    # Limit images with frame_limit
    if frame_limit > 0:
        list_img_file = list_img_file[:frame_limit];

    # Ignore some area
    det_object_ignore_area_list = [];
    if os.path.isfile(config.ignore_detection_area):
        det_object_ignore_area_list = DetObject.from_csv(config.ignore_detection_area, expand_mask = True);

    det_zone_IM = None;
    det_zone_IM_shrinked = None;
    if os.path.isfile(config.det_zone_im):
        det_zone_IM = det_zone.DetZoneImage.read_from_yml(config.det_zone_im);
        det_zone_IM_shrinked =  det_zone_IM.shrink_zone(config.shrink_zone);

    # Construct tracker
    tk_overlap = multiple_overlap_association.MultipleOverlapAssociation(associate_with_label, threshold_overlap, nb_frame_past, det_zone_IM= None);

    # Get name prefix
    name_prefix = '';
    if len(list_img_file) > 0:
        name_prefix = trajutil.get_name_prefix(list_img_file[0]);

    total_frame_index = len(list_img_file);
    __time_lap = time.time()
    logger.info(f'>>> initialization elapsed {__time_lap - __time_beg:.3f} seconds.')
    __time_beg = __time_lap

    for frame_index, image_name in enumerate(list_img_file):

        # Record start time for performance evaluation
        start_time = time.time()

        # Open frame
        frame = cv2.imread(os.path.join(config.image_dir, image_name));

        # CSV name management
        csv_name = image_name.split('.')[0] + '_det.csv';
        csv_path = os.path.join(config.det_dir, csv_name);

        if not os.path.exists(csv_path):
            logger.warning(f'skip {csv_path}')
            continue

        # Read detections
        det_object_list = DetObject.from_csv(csv_path, expand_mask = True);

        # Filter detections
        for det_object in list(det_object_list):
            '''
            1. 按类别剔除目标:
              1.1. vehicles    模式下仅处理 ['car', 'bus', truck', 'motorcycle']
              1.2. pedestrians 模式下仅处理 ['person', 'bicycle']
            2. 按检测质量剔除非 good
            3. 按检测区域剔除包围盒中心点不在检测区域内的
            '''
            # Delete the detection that are not in the label_list
            if not (det_object.label in label_list):
                det_object_list.remove(det_object);
                continue;

            # Remove det_object that are not good
            elif not det_object.good:
                det_object_list.remove(det_object);
                continue;

            # Delete dectection not in det zone:
            elif delete_det_out_det_zone:
                if not (det_zone_IM_shrinked is None):
                    if not det_zone_IM_shrinked.in_zone(det_object.get_center_det_2Dbox()):
                        det_object_list.remove(det_object);


        # 剔除与 ignore 区域 IOU 超过阈值的目标 TODO: 此处双重 for 循环是否有必要
        # Ignore det object that overlap with ignore area
        for det_object_ignore_area in det_object_ignore_area_list:
            for det_object in list(det_object_list):
                if det_object_file.intersection_rect(det_object.det_2Dbox, det_object_ignore_area.det_2Dbox) > 0 :
                    overlap = det_object_file.intersection_over_union_mask(det_object_ignore_area.det_mask, det_object.det_mask);

                    if overlap > 0.3:
                        det_object_list.remove(det_object);
                        print("Frame: {} Removing: because overlap:{} with det_ignore area".format(frame_index, det_object.det_id))

        # 基于 IOU 的关联匹配
        track_det_list = tk_overlap.push_detection(det_object_list, frame);

        status_str = '{} {}/{} Time: {}'.format(image_name, frame_index, total_frame_index, round((time.time() - start_time), 5 ));
        cfgutil.progress_bar(frame_index, total_frame_index, status_str)
        # print('\n ===> Execution ', frame_index, ' Time', round((time.time() - start_time), 5 ), '\n' )

        # Add annotation on Image:
        # 显示跟踪成功的目标，并以红色显示忽悠区域及检测收缩区域的目标
        if save_images or show_images:
            cv_image = cv2.imread(os.path.join(config.image_dir, image_name));

            if not (cv_image is None):
                for tk in tk_overlap.tracker_list_active:
                    frame_index = max(0, tk_overlap.frame_index - 1);

                    det_object = tk.get_det_frame_index(frame_index);
                    if not (det_object is None):
                        det_object.display_on_image(cv_image, track_id_text = True, color = tk.color);

                    for det_object_ignore_area in det_object_ignore_area_list:
                        det_object_ignore_area.display_on_image(cv_image, color = (0,0,255));

                    if not (det_zone_IM_shrinked is None):
                        det_zone_IM_shrinked.display_on_image(cv_image, color = (0,0,255));

                if show_images:
                    cv2.imshow('frame', cv_image)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                if save_images:
                    cv2.imwrite( os.path.join(overlap_img_dir, image_name), cv_image );

    __time_lap = time.time()
    logger.info(f'>>> loading data elapsed {__time_lap - __time_beg:.3f} seconds.')
    __time_beg = __time_lap

    # Get list of association tracker
    tracker_list = tk_overlap.get_tracker_list();

    # Save:
    if save_csv:
        track_2D.Track2D.export_det_asso_csv(list_img_file, tracker_list, overlap_csv_dir);

    __time_lap = time.time()
    logger.info(f'>>> export det association csv {__time_lap - __time_beg:.3f} seconds.')
    __time_beg = __time_lap

    # Run the tracking merge:
    tk_match_list = TrackMerge.run_merge_tracks(tracker_list, list_img_file, img_folder_path, det_zone_IM_shrinked, display=show_images);

    __time_lap = time.time()
    logger.info(f'>>> merge tracks elapsed {__time_lap - __time_beg:.3f} seconds.')
    __time_beg = __time_lap

    # Save the track merge
    tracks_merge_name = name_prefix + '_tracks_merge.csv'
    tracks_merge_path = os.path.join(output_dir, tracks_merge_name);
    TrackMerge.save_track_merge_csv(tracks_merge_path, tk_match_list);

    __time_lap = time.time()
    logger.info(f'>>> saving elapsed {__time_lap - __time_beg:.3f} seconds.')
    __time_beg = __time_lap

    return True;


if __name__ == '__main__':
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    ws = WorkSpace()
    save_dir = osp.join(ws.get_temp_dir(), get_name(__file__))
    if not osp.exists(save_dir):
        os.makedirs(save_dir)

    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
