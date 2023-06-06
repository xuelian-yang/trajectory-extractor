# -*- encoding: utf-8 -*-

import argparse
import copy
import cv2
from distinctipy import distinctipy
import logging
import numpy as np
import os.path as osp
import sys

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '..')))
from common.util import get_name, itti_argparse, itti_debug, itti_main, itti_timer, itti_traceback, save_json
from configs.workspace import WorkSpace

from traj_ext.tracker.cameramodel import CameraModel

sys.path.append(osp.dirname(__file__))
from itti_func import create_2d_array, get_time

@itti_traceback
@itti_argparse
def get_parser():
    parser = argparse.ArgumentParser(
        description='test calib')
    parser.add_argument('--py_file', type=str, default=__file__,
                        help='name of python file')
    parser.add_argument('-v', '--calib', type=str,
                        default='test_alaco/alaco_cameras/10.10.145.234_cfg.yml',
                        help='input calib file path')
    parser.add_argument('-i', '--image', type=str,
                        default='test_alaco/hdmap_calib/10.10.145.234.png',
                        help='input image file path')
    parser.add_argument('--output_dir', type=str,
                        default='',
                        help='Path of the output')
    parser.add_argument('--config_json', type=str,
                        default='',
                        help='Path to json config')
    args = parser.parse_args()
    return args


def write_sample(image, px_coords, enable_text=False):
    color_col = distinctipy.get_colors(len(px_coords), rng=99991)
    for idx in range(len(px_coords)):
        _color = [int(f * 255.0) for f in color_col[idx]]
        color_col[idx] = _color

    h, w, _ = image.shape
    print(f'>>> image: {image.shape}')
    for idx, item in enumerate(px_coords):
        p_w, p_h = item
        if 0 <= p_w < w and 0 <= p_h < h:
            if h == 2160:
                cv2.circle(image, item, 10, color_col[idx], 7)
            else:
                cv2.circle(image, item, 2, color_col[idx], 2)
            if enable_text:
                text = f'{idx}'
                if idx == 0:
                    text = 'O'
                if idx == 1:
                    text = 'X'
                if idx == 2:
                    text = 'Y'
                font_scale = 5
                if idx < 3:
                    font_scale = 2.0
                if h == 2160:
                    cv2.putText(image, text, item, cv2.FONT_HERSHEY_COMPLEX, font_scale, color_col[idx], 5)
                else:
                    cv2.putText(image, text, item, cv2.FONT_HERSHEY_COMPLEX, 1, color_col[idx], 1)
    line_width = 1
    if h == 2160:
        line_width = 3
    cv2.line(image, px_coords[0], px_coords[1], color_col[1], line_width)
    cv2.line(image, px_coords[0], px_coords[2], color_col[2], line_width)

    return image

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

    cam_model = CameraModel.read_from_yml(args.calib)
    logging.info(f'cam_model: {cam_model}')

    save_name = get_name(args.image)
    im = cv2.imread(args.image)
    pt = [
            np.array([0, 0, 0], dtype=np.float32),
            np.array([15, 0, 0], dtype=np.float32),
            np.array([0, 25, 0], dtype=np.float32),
            np.array([-5, -10, 0], dtype=np.float32),
            np.array([5, -10, 0], dtype=np.float32),
            np.array([5, 10, 0], dtype=np.float32),
            np.array([-5, 10, 0], dtype=np.float32),
          ]

    # ======================================================================== #
    # < 0 initial >
    # ======================================================================== #
    im_0 = copy.deepcopy(im)
    list_pt_m_0 = cam_model.project_list_pt_F(pt)
    print(f'>>> list_pt_m_0: {type(list_pt_m_0)} {list_pt_m_0}')
    im_0 = write_sample(im_0, list_pt_m_0, True)
    cv2.imwrite(osp.join(save_dir, f'00_initial-viz_{save_name}.png'), im_0)

    # ======================================================================== #
    # < 1 scale >
    # ======================================================================== #
    scale_x = 0.171875
    scale_y = 0.156018519
    print(f'>>> {scale_x} * 4096 = {scale_x * 4096.}')
    print(f'>>> {scale_y} * 2160 = {scale_y * 2160.}')
    dst_w, dst_h = 704, 337
    im_1 = cv2.resize(im, (dst_w, dst_h))
    cv2.imwrite(osp.join(save_dir, f'10_scale_{save_name}.png'), im_1)
    cam_model_1 = copy.deepcopy(cam_model)
    cam_model_1.apply_scale_factor(scale_x, scale_y)

    list_pt_m_1 = cam_model_1.project_list_pt_F(pt)
    print(f'>>> list_pt_m_1: {type(list_pt_m_1)} {list_pt_m_1}')
    im_1 = write_sample(im_1, list_pt_m_1)
    cv2.imwrite(osp.join(save_dir, f'11_scale-viz_{save_name}.png'), im_1)

    # ======================================================================== #
    # < 2 scale & crop >
    # ======================================================================== #
    crop_w, crop_h = 0, 81
    im_2 = cv2.resize(im, (dst_w, dst_h))
    im_2 = im_2[crop_h:, crop_w:, :]
    cv2.imwrite(osp.join(save_dir, f'20_scale-crop_{save_name}.png'), im_2)
    cam_model_2 = copy.deepcopy(cam_model)
    cam_model_2.apply_scale_factor(scale_x, scale_y)

    list_pt_m_2 = cam_model_2.project_list_pt_F(pt)
    list_pt_m_2 = [(t_w, t_h - crop_h) for t_w, t_h in list_pt_m_2]
    print(f'>>> list_pt_m_2: {type(list_pt_m_2)} {list_pt_m_2}')
    im_2 = write_sample(im_2, list_pt_m_2)
    cv2.imwrite(osp.join(save_dir, f'21_scale-crop-viz_{save_name}.png'), im_2)

if __name__ == '__main__':
    main(py_file=__file__)
