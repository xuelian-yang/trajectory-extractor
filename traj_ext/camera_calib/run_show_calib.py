# -*- coding: utf-8 -*-

"""
cd traj_ext/camera_calib/

set home_path=E:/Github/trajectory-extractor/traj_ext/camera_calib/calib_file/brest
python run_show_calib.py ^
  --camera_calib %home_path%/brest_area1_street_cfg.yml ^
  --image %home_path%/brest_area1_street.jpg ^
  --detection_zone %home_path%/brest_area1_detection_zone.yml

set home_path=E:/Github/trajectory-extractor/test_alaco/hdmap_calib
python run_show_calib.py ^
  --camera_calib %home_path%/10.10.145.231_cfg.yml ^
  --image %home_path%/10.10.145.231.png ^
  --detection_zone %home_path%/_detection_zone.yml
"""

# import the necessary packages
import argparse
import cv2
import sys
import os
import os.path as osp
import platform
import numpy as np
import time
import copy
from scipy.optimize import linear_sum_assignment
import configparser

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '../..')))
from traj_ext.tracker import cameramodel
from traj_ext.utils import det_zone

isWindows = (platform.system() == "Windows")

windows, win_w, win_h = [], 1920, 1080
names = ["image_1"]
for win_name in names:
    if win_name not in windows:
        windows.append(win_name)
        if isWindows:
            cv2.namedWindow(str(win_name), cv2.WINDOW_NORMAL)
        else:
            cv2.namedWindow(str(win_name), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow(str(win_name), win_w, win_h)


def click(event, x, y, flags, param ):

    # if the left mouse button was clicked, record the starting
    # (x, y) coordinates and indicate that cropping is being
    # performed

    pt_image_list = param[0]
    cam_model_1 = param[1];
    image_1 = param[2];
    det_zone_FNED = param[3];

    if event == cv2.EVENT_LBUTTONDOWN:
        pt_image = (x, y)
        pt_image_list.append(pt_image);

        draw_image(image_1, cam_model_1, pt_image_list, det_zone_FNED);
    return


def draw_image(image_1, cam_model_1, pt_image_list, det_zone_FNED = None):

    if not (cam_model_1 is None):
        image_1_temp = copy.copy(image_1);

        # Show origin of the frame
        print('\nSummary: Position of selected points');
        pt_origin = cam_model_1.project_points(np.array([0.0,0.0,0.0]));
        cv2.circle(image_1_temp, (pt_origin[0], pt_origin[1]), 2, (0,255, 255), -1)
        print('Point Origin: {} FNED: {}'.format(pt_origin, np.array([0.0,0.0,0.0]).transpose()));


        pt_FNED_list_temp = [];
        for index, pt_image in enumerate(pt_image_list):
            # for pt_i in pt_image_list:
            pos_FNED = cam_model_1.projection_ground(0, pt_image);
            pos_FNED.shape = (3,1);
            pt_FNED_list_temp.append(pos_FNED);

            # Show mask of the region of interest
            cv2.putText(image_1_temp, str(index), pt_image, cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
            cv2.circle(image_1_temp, pt_image, 2, (0,0, 255), -1)

            print('Point {}: {} FNED: {}'.format(index, pt_image, pos_FNED.transpose()));


        # Draw det zone:
        if not (det_zone_FNED is None):
            det_zone_FNED.display_on_image(image_1_temp, cam_model_1);
        cv2.imshow("image_1", image_1_temp)


def main():

    # Print instructions
    print("############################################################")
    print("Camera Calibration viewer")
    print("############################################################\n")

    # ##########################################################
    # # Parse Arguments
    # ##########################################################
    argparser = argparse.ArgumentParser(
        description='Camera calibration viewer')
    argparser.add_argument(
        '-c', '--camera_calib',
        help='Camera calib file',
        required=True)
    argparser.add_argument(
        '-i', '--image',
        help='Camera image',
        required=True)
    argparser.add_argument(
        '-d', '--detection_zone',
        help='Detection Zone')
    args = argparser.parse_args();

    # ##########################################################
    # # Read config file:
    # ##########################################################

    # Print instructions
    print("Instruction:")
    print("    - Click on the image to select a point")
    print("    - Press 'd' to delete last point, coordinates are displayed in the console")
    print("    - Press 'q' to exit\n")

    # Construct camera model
    cam_model_1 = None;

    if args.camera_calib != '':
        cam_model_1 = cameramodel.CameraModel.read_from_yml(args.camera_calib);

    # load the image, clone it, and setup the mouse callback function
    image_1 = cv2.imread(args.image)
    if image_1 is None:
        print('\n[Error]: camera_img_sat_path is not valid: {}'.format(args.image));
        return;


    # Det zone:
    det_zone_FNED = None;
    if args.detection_zone:
        det_zone_FNED = det_zone.DetZoneFNED.read_from_yml(args.detection_zone);

    # Create windows
    cv2.namedWindow("image_1")

    pt_image_list = [];
    cv2.setMouseCallback("image_1", click, param=(pt_image_list, cam_model_1, image_1, det_zone_FNED))

    draw_image(image_1, cam_model_1, pt_image_list, det_zone_FNED);

    # keep looping until the 'q' key is pressed
    save = False;
    while True:

        # display the image and wait for a keypress
        key = cv2.waitKey(1) & 0xFF
        # if key == ord("c"):
        # if the 'Enter' key is pressed, end of the program
        if key == 13:
            save = True;
            break

        elif  key == ord("q"):
            return;

        elif key == ord("d"):
            if len(pt_image_list) > 0:
                pt_image_list.pop();
                draw_image(image_1, cam_model_1, pt_image_list, det_zone_FNED);


    print("Program Exit\n")
    print("############################################################\n")


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
