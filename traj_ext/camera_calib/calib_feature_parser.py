# -*- coding: utf-8 -*-

"""
将 labelme 标注的图像特征点坐标 与 QGIS 导出的经纬度坐标进行组合, 生成 trajectory-extractor 格式的标定输入.

conda activate traj
cd E:\Github\trajectory-extractor

python traj_ext/camera_calib/calib_feature_parser.py
"""

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
import sys
from termcolor import colored
import time

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '../..')))
from common.util import setup_log, d_print, get_name, d_print_b, d_print_g, d_print_r, d_print_y
from configs.workspace import WorkSpace

logger = logging.getLogger(__name__)


class DataLabelme:
    def __init__(self, json_path):
        self.json_path = json_path

        self.has_data = False
        self.im_path = None
        self.im_w = None
        self.im_h = None
        self.geometry_points = None

        self.check_data()
        self.parse_data()

        self.debug()

    def check_data(self):
        if not osp.exists(self.json_path):
            raise ValueError(f'file not exist: {self.json_path}')

    def parse_data(self):
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

class DataQGis:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.check_data()
        self.parse_data()

    def check_data(self):
        if not osp.exists(self.csv_path):
            raise ValueError(f'file not exist: {self.csv_path}')

    def parse_data(self):
        reader = csv.DictReader(self.csv_path)

        for row in reader:
            d_print_y(f'row: {type(row)} {row}')
        form = pd.read_csv(self.csv_path, encoding='gb2312')
        print(form)
        pass


def gen_pair(save_dir):
    input_dir = osp.abspath(osp.join(osp.dirname(__file__), '../../test_alaco/hdmap_calib'))
    if not osp.exists(input_dir):
        raise ValueError(f'path not exist: {input_dir}')
    labelme_file = 'feature_points_10.10.145.231.json'
    qgis_file = 'point_label_latlog.csv'

    data_labelme = DataLabelme(osp.join(input_dir, labelme_file))
    data_qgis = DataQGis(osp.join(input_dir, qgis_file))
    pass


if __name__ == "__main__":
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    ws = WorkSpace()
    save_dir = osp.join(ws.get_temp_dir(), get_name(__file__))
    if not osp.exists(save_dir):
        os.makedirs(save_dir)

    gen_pair(save_dir)

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
