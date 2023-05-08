# -*- coding: utf-8 -*-

"""
将 labelme 标注的图像特征点坐标 与 QGIS 导出的经纬度坐标进行组合, 生成 trajectory-extractor 格式的标定输入.

conda activate traj
cd E:\Github\trajectory-extractor

python traj_ext/camera_calib/calib_feature_parser.py --labelme_json feature_points_10.10.145.232.json

python run_calib_stereo.py
"""

import argparse
import copy
import csv
import cv2
from datetime import datetime
from distinctipy import distinctipy
import json
import logging
import math
from matplotlib import pyplot as plt
import numpy as np
import os
import os.path as osp
import pandas as pd
import platform
import sys
from termcolor import colored
import time


sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '../..')))
from common.util import setup_log, d_print, get_name, d_print_b, d_print_g, d_print_r, d_print_y
from configs.workspace import WorkSpace

logger = logging.getLogger(__name__)
isWindows = (platform.system() == "Windows")

class DataLabelme:
    """Labelme 标注的特征点坐标."""
    def __init__(self, json_path, save_dir):
        self.json_path = json_path
        self.save_dir = save_dir

        self.has_data = False
        self.im_path = None
        self.im_w = None
        self.im_h = None
        self.geometry_points = None

        self.check_data()
        self.parse_data()

        # self.debug()

    def check_data(self):
        if not osp.exists(self.json_path):
            raise ValueError(f'file not exist: {self.json_path}')

    def parse_data(self):
        """从 json 文件读取点坐标及名称."""
        json_dict = json.load(open(self.json_path, 'r'))
        self.im_path = osp.join(osp.dirname(self.json_path), json_dict['imagePath'])
        self.im_w = json_dict['imageWidth']
        self.im_h = json_dict['imageHeight']

        # 读取点集
        self.geometry_points = dict()
        data_shapes = json_dict['shapes']
        n = len(data_shapes)
        for i in range(n):
            if data_shapes[i]['shape_type'] != 'point':
                continue
            self.geometry_points[data_shapes[i]['label']] = data_shapes[i]['points'][0]
            self.has_data = True

    def debug(self):
        self.print_points()
        print(f'{self.im_path}: {self.im_h} x {self.im_w}')

    def print_points(self):
        print(f'{len(self.geometry_points)}')
        for k, v in self.geometry_points.items():
            print(f'{k}: {v[0]} {v[1]}')

    def get_points(self):
        return self.geometry_points

    def get_img_path(self):
        return self.im_path


class DataQGis:
    """QGIS 标注的特征点经纬度坐标."""
    def __init__(self, csv_path, save_dir):
        self.csv_path = csv_path
        self.save_dir = save_dir

        self.has_data = False
        self.geometry_points = None
        self.feature_names = None

        self.check_data()
        self.parse_data()

    def check_data(self):
        if not osp.exists(self.csv_path):
            raise ValueError(f'file not exist: {self.csv_path}')

    def parse_data(self):
        """读取经纬度坐标及名称.
        latitude: 纬度
        longitude: 经度
        """
        df = pd.read_csv(self.csv_path, encoding='gb2312')
        self.geometry_points = dict()
        for ind in df.index:
            self.has_data = True
            logger.debug(f"{df['name'][ind]} {df['Y'][ind]} {df['X'][ind]}")
            # trajectory-extractor 格式为 (纬度, 经度)
            self.geometry_points[df['name'][ind]] = ([df['Y'][ind], df['X'][ind]], df['desc'][ind])
        self.feature_names = list(self.geometry_points.keys())

    def get_points(self):
        return self.geometry_points

    def get_latlon_by_name(self, feat_name, ret_desc=False):
        assert feat_name in self.feature_names
        latlon, feat_desc = self.geometry_points[feat_name]
        if ret_desc:
            return latlon, feat_desc
        return latlon


def gen_pair(save_dir, labelme_json):
    """
    将 labelme 标注的图像特征点坐标 与 QGIS 导出的经纬度坐标进行组合, 生成 trajectory-extractor 格式的标定输入.
    """
    input_dir = osp.abspath(osp.join(osp.dirname(__file__), '../../test_alaco/hdmap_calib'))
    if not osp.exists(input_dir):
        raise ValueError(f'path not exist: {input_dir}')
    # labelme_file = 'feature_points_10.10.145.231.json'
    labelme_file = labelme_json
    qgis_file = 'point_label_latlog.csv'

    data_labelme = DataLabelme(osp.join(input_dir, labelme_file), save_dir)
    data_qgis = DataQGis(osp.join(input_dir, qgis_file), save_dir)

    labelme_points = data_labelme.get_points()
    # 中心点
    orig_name = 'cross_e_01'
    orig_latlon, orig_desc = data_qgis.get_latlon_by_name(orig_name, True)

    # 参考 traj_ext/camera_calib/calib_file/brest/brest_area1_street_hd_map.csv 格式
    with open(osp.join(save_dir, labelme_file + '_hd_map.csv'), 'wt') as f_ou:
        f_ou.write('point_type,point_id,x_ned,y_ned,latitude,longitude,origin_latitude,origin_longitude\n')
        for idx, (k, v) in enumerate(labelme_points.items()):
            latlon, desc = data_qgis.get_latlon_by_name(k, True)
            d_print_y(f'{idx:2d} {k:20s} {v} {latlon} {desc}')
            f_ou.write(f'100,{idx},{v[0]},{v[1]},{latlon[0]},{latlon[1]},{orig_latlon[0]},{orig_latlon[1]}\n')

    # 参考 python run_calib_manual.py -init 生成的 camera_calib_manual_latlon.csv 格式
    path_manual_csv = osp.abspath(osp.join(save_dir, labelme_file + '_camera_calib_manual_latlon.csv'))
    with open(path_manual_csv, 'wt') as f_ou:
        f_ou.write('pixel_x,pixel_y,lat_deg,lon_deg,origin_lat_deg,origin_lon_deg\n')
        for k, v in labelme_points.items():
            latlon, desc = data_qgis.get_latlon_by_name(k, True)
            f_ou.write(f'{int(v[0])},{int(v[1])},{latlon[0]},{latlon[1]},{orig_latlon[0]},{orig_latlon[1]}\n')

    # run_calib_manual.py 脚本
    if isWindows:
        d_print_r(f'\ncd traj_ext/camera_calib/\n'
                  f'python run_calib_manual.py ^\n'
                  f'  -calib_points {path_manual_csv} ^\n'
                  f'  -image {data_labelme.get_img_path()}\n')
    else:
        d_print_r(f'\ncd traj_ext/camera_calib/\n'
                  f'python run_calib_manual.py \\\n'
                  f'  -calib_points {path_manual_csv} \\\n'
                  f'  -image {data_labelme.get_img_path()}\n')


def main():
    argparser = argparse.ArgumentParser(
        description='generate feature point files for calibration')
    argparser.add_argument('--labelme_json', default='feature_points_10.10.145.231.json')
    args = argparser.parse_args()

    ws = WorkSpace()
    save_dir = osp.join(ws.get_temp_dir(), get_name(__file__))
    if not osp.exists(save_dir):
        os.makedirs(save_dir)

    gen_pair(save_dir, args.labelme_json)


if __name__ == "__main__":
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    main()

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
