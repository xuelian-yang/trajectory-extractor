# -*- coding: utf-8 -*-

"""
手动设置检测区域.

set home_path=traj_ext/camera_calib/calib_file/brest
python traj_ext/camera_calib/run_detection_zone.py ^
  -camera_street %home_path%/brest_area1_street_cfg.yml ^
  -image_street %home_path%/brest_area1_street.jpg ^
  -camera_sat %home_path%/brest_area1_sat_cfg.yml ^
  -image_sat %home_path%/brest_area1_sat.png ^
  -output_name brest

set camera_ip=10.10.145.232
python traj_ext/camera_calib/run_detection_zone.py ^
  -camera_street test_alaco/alaco_cameras/%camera_ip%_cfg.yml ^
  -image_street test_alaco/hdmap_calib/%camera_ip%.png ^
  -camera_sat test_alaco/alaco_cameras/hdmap_0_cfg.yml ^
  -image_sat test_alaco/hdmap_calib/hdmap_0.png ^
  -output_name %camera_ip%

set camera_ip=10.10.145.232
set camera_targ=10.10.145.233
python traj_ext/camera_calib/run_detection_zone.py ^
  -camera_street test_alaco/alaco_cameras/%camera_ip%_cfg.yml ^
  -image_street test_alaco/hdmap_calib/%camera_ip%.png ^
  -camera_sat test_alaco/alaco_cameras/%camera_targ%_cfg.yml ^
  -image_sat test_alaco/hdmap_calib/%camera_targ%.png ^
  -output_name %camera_ip%
"""

# import the necessary packages
import argparse
import cv2
import logging
import sys
import os
import os.path as osp
import platform
import numpy as np
from termcolor import colored
import time
import copy

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '../..')))
from traj_ext.tracker.cameramodel import CameraModel
from traj_ext.camera_calib.adaptive_win_size import *

from traj_ext.camera_calib import calib_utils
from traj_ext.object_det import det_object
from traj_ext.utils import det_zone

from common.util import *
from configs.workspace import *

logger = logging.getLogger(__name__)
isWindows = (platform.system() == "Windows")
isLinux = (platform.system() == "Linux")

names = ['Step: run_detection_zone - image_1', 'Step: run_detection_zone - image_2']

def click(event, x, y, flags, param ):
    # logger.info(f'click(..)')

    # if the left mouse button was clicked, record the starting
    # (x, y) coordinates and indicate that cropping is being
    # performed

    pt_image_list = param[0]
    cam_model_1 = param[1];
    image_1 = param[2];
    cam_model_2 = param[3];
    image_2 = param[4];

    if event == cv2.EVENT_LBUTTONDOWN:
        pt_image = (x, y)
        pt_image_list.append(pt_image);

        draw_image(image_1, image_2, cam_model_1, cam_model_2, pt_image_list, names[0], names[1]);
    return


def draw_image(image_1, image_2, cam_model_1, cam_model_2, pt_image_list, win_name1, win_name2):
    logger.info(f'draw_image(..)')

    if not (cam_model_1 is None)  and  not (image_2 is None) and not (cam_model_2 is None):
        # image_1_temp = copy.copy(image_1);
        # image_2_temp = copy.copy(image_2);
        image_1_temp, image_2_temp = image_1, image_2

        pt_FNED_list_temp = [];
        for index, pt_image in enumerate(pt_image_list):
            # for pt_i in pt_image_list:
            pos_FNED = cam_model_1.projection_ground(0, pt_image);
            pos_FNED.shape = (3,1);
            pt_FNED_list_temp.append(pos_FNED);

            # Show mask of the region of interest
            cv2.putText(image_1_temp, str(index), pt_image, cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
            cv2.circle(image_1_temp, pt_image, 2, (0, 0, 255), -1)

        logging.info(f'(0) >>> pos_FNED: {type(pos_FNED)} {pos_FNED}')
        logging.info(f'(0) >>> pt_image_list: {len(pt_image_list)} {pt_image_list}')
        logging.info(f'(1) >>> pt_FNED_list_temp: {type(pt_FNED_list_temp)} {len(pt_FNED_list_temp)} {pt_FNED_list_temp}')

        if len(pt_FNED_list_temp) > 1:

            list_pt_im = cam_model_1.project_list_pt_F(pt_FNED_list_temp);
            mask_1 = det_object.create_mask_image((image_1_temp.shape[0], image_1_temp.shape[1]), list_pt_im);
            det_object.draw_mask(image_1_temp, mask_1, (255, 0, 255))

            list_pt_im = cam_model_2.project_list_pt_F(pt_FNED_list_temp);
            mask_2 = det_object.create_mask_image((image_2_temp.shape[0], image_2_temp.shape[1]), list_pt_im);
            det_object.draw_mask(image_2_temp, mask_2, (255, 0, 255))

        cv2.imshow(win_name2, image_2_temp)
        cv2.imshow(win_name1, image_1_temp)

    else:
        # image_1_temp = copy.copy(image_1);
        image_1_temp = image_1

        for index, pt_image in enumerate(pt_image_list):

            # Show mask of the region of interest
            cv2.putText(image_1_temp, str(index), pt_image, cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
            cv2.circle(image_1_temp, pt_image, 2, (0,0, 255), -1)

        list_pt_im = cam_model_1.project_list_pt_F(pt_FNED_list_temp);
        mask_1 = det_object.create_mask_image((image_1_temp.shape[0], image_1_temp.shape[1]), list_pt_im);
        det_object.draw_mask(image_1_temp, mask_1, (0,0,255));

        # cv2.imshow("image_1", image_1_temp)
        cv2.imshow(win_name1, image_1_temp)


def run_detection_zone(cam_model_street_path, image_street_path, cam_model_sat_path, image_sat_path, output_name, save_dir):
    logger.info(f'run_detection_zone({cam_model_street_path}, {image_street_path}, {cam_model_sat_path}, {image_sat_path}, {output_name}, {save_dir})')
    # Print instructions
    print("Instruction:")
    print("    - Click on the image to define the detection zone")
    print("    - Press 'd' to delete last point")
    print("    - Press Enter to save the detection file")
    print("    - Press 'q' to exit without saving detection zone file \n")

    # Construct camera model
    cam_model_1 = None;
    if os.path.isfile(cam_model_street_path):
        cam_model_1 = CameraModel.read_from_yml(cam_model_street_path);
    else:
        print('\n[Error]: Camera Street model not found: {}'.format(cam_model_street_path))
        return;

    # load the image, clone it, and setup the mouse callback function
    image_1 = None;
    if os.path.isfile(image_street_path):
        image_1 = cv2.imread(image_street_path)
    else:
        print('\n[Error]: image_street_path is not valid: {}'.format(image_street_path));
        return;

    cam_model_2 = None;
    if os.path.isfile(cam_model_sat_path):
        cam_model_2 = CameraModel.read_from_yml(cam_model_sat_path);
    else:
        print('\n[Error]: Camera Street model not found: {}'.format(cam_model_sat_path))
        return;

    # load the image, clone it, and setup the mouse callback function
    image_2 = None;
    if os.path.isfile(image_sat_path):
        image_2 = cv2.imread(image_sat_path)
    else:
        print('\n[Error]: image_sat_path is not valid: {}'.format(image_sat_path));
        return;

    # Create windows
    win_scale_1 = find_scale(image_1, 2)
    win_scale = win_scale_1
    if image_2 is not None:
        win_scale_2 = find_scale(image_2, 2)
        win_scale = max(win_scale_1, win_scale_2)

    im_h_1, im_w_1, _ = image_1.shape
    win_w_1 = im_w_1 // win_scale
    win_h_1 = im_h_1 // win_scale

    win_name_1 = names[0]
    win_name_2 = names[1]

    cv2.namedWindow(win_name_1, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name_1, win_w_1, win_h_1)
    cv2.moveWindow(win_name_1, 0, 0)

    if not (image_2 is None):
        im_h_2, im_w_2, _ = image_2.shape
        win_w_2 = im_w_2 // win_scale
        win_h_2 = im_h_2 // win_scale

        cv2.namedWindow(win_name_2, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name_2, win_w_2, win_h_2)
        cv2.moveWindow(win_name_2, 1920 // 2, 0)

    pt_image_list = [];
    cv2.setMouseCallback(win_name_1, click, param=(pt_image_list, cam_model_1, image_1, cam_model_2, image_2))

    cv2.imshow(win_name_1, image_1)
    if not (image_2 is None):
        cv2.imshow(win_name_2, image_2)

    # keep looping until the 'q' key is pressed
    save_zone = False;
    while True:
        # display the image and wait for a keypress
        key = cv2.waitKey(1) & 0xFF
        # if key == ord("c"):
        # if the 'Enter' key is pressed, end of the program
        if key == 13:
            save_zone = True;
            break

        elif  key == ord("q"):
            return;

        elif key == ord("d"):
            if len(pt_image_list) > 0:
                pt_image_list.pop();
                draw_image(image_1, image_2, cam_model_1, cam_model_2, pt_image_list, win_name_1, win_name_2);

    # save image
    save_name = osp.join(save_dir, f'run_detection_zone_{osp.basename(image_street_path)}')
    cv2.imwrite(save_name, image_1)
    save_name = osp.join(save_dir, f'run_detection_zone_{osp.basename(image_sat_path)}')
    cv2.imwrite(save_name, image_2)

    # Make sure there is enough point
    if not len(pt_image_list) > 2:
        print('[Error]: Not enough points to define the detection zone (3 points minimum): {}'.format(pt_image_list))
        return

    if not (cam_model_1 is None):
        model_points_FNED = np.array([]);
        model_points_FNED.shape = (0,3);

        # Convert the point in pixel in point in FNED
        for index, pt_image in enumerate(pt_image_list):

            print(pt_image)

            pos_FNED = cam_model_1.projection_ground(0, pt_image);

            pos_FNED.shape = (1,3);
            model_points_FNED = np.append(model_points_FNED, pos_FNED, axis=0);

        # Only keep convex hull
        model_points_FNED_convex = calib_utils.convex_hull(model_points_FNED);
        det_zone_FNED = det_zone.DetZoneFNED(model_points_FNED_convex);

        if save_zone:

            # Define output name
            output_name_det = output_name + '_detection_zone.yml'
            # output_path = os.path.join(os.path.dirname(cam_model_street_path), output_name_det)
            output_path = os.path.join(save_dir, output_name_det)

            # Write Param in YAML file
            det_zone_FNED.save_to_yml(output_path)

    model_points_IM = np.array([]);
    model_points_IM.shape = (0,2);

    # Convert the point in pixel in point in FNED
    for index, pt_image in enumerate(pt_image_list):

        pt = np.array(pt_image);
        pt.shape = (1,2);

        model_points_IM = np.append(model_points_IM, pt, axis=0);

    # Only keep convex hull
    model_points_IM_convex = calib_utils.convex_hull(model_points_IM);
    det_zone_IM = det_zone.DetZoneImage(model_points_IM_convex);

    if save_zone:

        # Define output name
        output_name_det_im = output_name + '_detection_zone_im.yml'
        # output_im_path = os.path.join(os.path.dirname(cam_model_street_path), output_name_det_im)
        output_im_path = os.path.join(save_dir, output_name_det_im)

        # Write Param in YAML file
        det_zone_IM.save_to_yml(output_im_path)

    print("\nProgram Exit")
    print("############################################################\n")


def main():
    logger.info(f'main()')
    # Print instructions
    print("############################################################")
    print("Camera Detection Zone")
    print("############################################################\n")

    # ##########################################################
    # # Parse Arguments
    # ##########################################################
    argparser = argparse.ArgumentParser(
        description='Camera detection zone')
    argparser.add_argument(
        '-camera_street', dest="cam_model_street_path",
        default='',
        help='Path of the street camera model yml')
    argparser.add_argument(
        '-image_street', dest="image_street_path",
        default='',
        help='Path to the image street')
    argparser.add_argument(
        '-camera_sat', dest="cam_model_sat_path",
        default='',
        help='Path of the satellite camera model yml')
    argparser.add_argument(
        '-image_sat', dest="image_sat_path",
        default='',
        help='Path to the image satellite')
    argparser.add_argument(
        '-output_name', dest="output_name",
        default='',
        help='Name of the output files')
    args = argparser.parse_args()
    for item in vars(args):
        logger.info(f'{item:20s} : {getattr(args, item)}')

    ws = WorkSpace()
    save_dir = osp.join(ws.get_temp_dir(), get_name(__file__))
    if not osp.exists(save_dir):
        os.makedirs(save_dir)

    # Run camera calibration
    run_detection_zone(args.cam_model_street_path, args.image_street_path, args.cam_model_sat_path, args.image_sat_path, args.output_name, save_dir)


if __name__ == '__main__':
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
