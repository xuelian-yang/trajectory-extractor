# -*- encoding: utf-8 -*-

# @File        :   mono_tracking.py
# @Description :   单目跟踪
# @Time        :   2023/05/12 13:51:37
# @Author      :   Xuelian.Yang
# @Contact     :   Xuelian.Yang@geely.com
# @LastEditors :   Xuelian.Yang
# @Example     :   python mono_tracking.py --show_images --img_scale 0.2

# here put the import lib
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
from multiprocessing.dummy import Pool as ThreadPool
import numpy as np
import os
import os.path as osp
import pandas as pd
import platform
import sys
from termcolor import colored
import threading
from threading import Thread
import time

FILE_PATH = osp.abspath(osp.dirname(__file__))
sys.path.append(osp.join(FILE_PATH, '../..'))

from traj_ext.box3D_fitting import Box3D_utils

from traj_ext.object_det.mask_rcnn import detect_utils
from traj_ext.tracker import cameramodel

from traj_ext.utils import cfgutil
from traj_ext.utils.mathutil import *

from traj_ext.object_det import det_object
from traj_ext.utils import det_zone
from traj_ext.box3D_fitting import box3D_object

from common.util import setup_log, d_print, get_name, d_print_b, d_print_g, d_print_r, d_print_y
from configs.workspace import WorkSpace

from traj_ext.object_det.det_object import DetObject
ROOT_DIR_MASKRCNN = osp.abspath(osp.join(FILE_PATH, './traj_ext/object_det/mask_rcnn/Mask_RCNN'))
sys.path.append(ROOT_DIR_MASKRCNN)  # To find local version of the library
from mrcnn import utils
import mrcnn.model as modellib
from mrcnn import visualize

# Import COCO config
from samples.coco import coco

logger = logging.getLogger(__name__)
isWindows = (platform.system() == "Windows")


class_names = ['BG', 'person', 'bicycle', 'car', 'motorcycle', 'airplane',
               'bus', 'train', 'truck', 'boat', 'traffic light',
               'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird',
               'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
               'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
               'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
               'kite', 'baseball bat', 'baseball glove', 'skateboard',
               'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
               'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
               'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
               'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
               'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
               'keyboard', 'cell phone', 'microwave', 'oven', 'toaster',
               'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
               'teddy bear', 'hair drier', 'toothbrush']

class LoadStreams:
    """
    References
    ----------
    yolov8_tracking/yolov8/ultralytics/yolo/data/dataloaders/stream_loaders.py
    """
    def __init__(self, sources, vid_stride, max_frame):
        self.vid_stride = vid_stride
        assert isinstance(sources, list) and len(sources) > 0 and isinstance(sources[0], str)

        n = len(sources)
        self.sources = sources
        self.imgs, self.fps, self.frames, self.threads, self.caps, self.num_frames = [None] * n, [0] * n, [0] * n, [None] * n, [None] * n, [None] * n
        self.is_mp4 = sources[0].endswith('.mp4')

        for i, s in enumerate(sources):
            st = f'{i + 1}/{n}: {s}... '
            self.caps[i] = cv2.VideoCapture(s)
            self.num_frames[i] = 0
            assert self.caps[i].isOpened(), f'{st}Failed to open {s}'
            w = int(self.caps[i].get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.caps[i].get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.caps[i].get(cv2.CAP_PROP_FPS)  # warning: may return 0 or nan
            self.frames[i] = max(int(self.caps[i].get(cv2.CAP_PROP_FRAME_COUNT)), 0) or float('inf')  # infinite stream fallback
            if self.is_mp4 and self.frames[i] > max_frame:
                self.frames[i] = max_frame
                d_print(f'>> {self.frames[i]}')
            self.fps[i] = max((fps if math.isfinite(fps) else 0) % 100, 0) or 30  # 30 FPS fallback

            _, self.imgs[i] = self.caps[i].read()  # guarantee first frame
            self.threads[i] = Thread(target=self.update, args=([i, self.caps[i], s]), daemon=True)
            logging.info(f"{st} Success ({self.frames[i]} frames {w}x{h} at {self.fps[i]:.2f} FPS)")
            self.threads[i].start()

    def update(self, i, cap, stream):
        # Read stream `i` frames in daemon thread
        n, f = 0, self.frames[i]  # frame number, frame array
        while cap.isOpened() and n < f and not self.is_mp4:
            n += 1
            cap.grab()  # .read() = .grab() followed by .retrieve()
            if n % self.vid_stride == 0:
                success, im = cap.retrieve()
                if success:
                    self.imgs[i] = im
                    self.num_frames[i] = n
                else:
                    self.imgs[i] = np.zeros_like(self.imgs[i])
                    cap.open(stream)  # re-open stream if signal was lost
            time.sleep(0.0)  # wait time

    def __iter__(self):
        self.count = -1
        return self

    def __next__(self):
        self.count += 1
        if not self.is_mp4:
            if not all(x.is_alive() for x in self.threads) or cv2.waitKey(1) == ord('q'):  # q to quit
                cv2.destroyAllWindows()
                raise StopIteration
        else:
            for i, cap in enumerate(self.caps):
                cap.grab()
                self.num_frames[i] += 1
                success, im = cap.retrieve()
                if success and self.num_frames[i] < self.frames[i]:
                    self.imgs[i] = im
                elif self.num_frames[i] >= self.frames[i] - 2:
                    logging.warning(f'stop iteration {self.count} with video [{i}]')
                    cap.release()
                    logging.warning(f'no new frame data, StopIteration {self.count}')
                    cv2.destroyAllWindows()
                    raise StopIteration
        return self.sources, im

    def __len__(self):
        return len(self.sources)  # 1E12 frames = 32 streams at 30 FPS for 30 years


class InferenceConfig(coco.CocoConfig):
    # Set batch size to 1 since we'll be running inference on
    # one image at a time. Batch size = GPU_COUNT * IMAGES_PER_GPU
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1


def load_model():
    MODEL_DIR = os.path.join(ROOT_DIR_MASKRCNN, "logs")
    COCO_MODEL_PATH = os.path.join(ROOT_DIR_MASKRCNN, "mask_rcnn_coco.h5")
    if not os.path.exists(COCO_MODEL_PATH):
        utils.download_trained_weights(COCO_MODEL_PATH)
    config_inf = InferenceConfig()
    config_inf.display()
    model = modellib.MaskRCNN(mode="inference", model_dir=MODEL_DIR, config=config_inf)
    model.load_weights(COCO_MODEL_PATH, by_name=True)
    return model


class MonoTracking:
    def __init__(self, config):
        d_print_y(f'config: {type(config)} {config}')
        self.config = config
        self.video_path = config.video_path
        self.skip = config.skip
        self.max_frame = config.max_frame
        self.show_images = config.show_images
        self.output_dir = config.output_dir

    def run(self):
        dataset = LoadStreams([self.video_path], self.skip, self.max_frame)
        model = load_model()

        ##########################################################
        # Camera Parameters
        ##########################################################
        cam_model_1 = cameramodel.CameraModel.read_from_yml(self.config.camera_model);
        cam_scale_factor = self.config.img_scale;
        if cam_scale_factor < 0:
            print('[ERROR]: Image scale factor < 0: {}'.format(cam_scale_factor))
        cam_model_1.apply_scale_factor(cam_scale_factor,cam_scale_factor);
        # Create pool of thead
        pool = ThreadPool(50)
        type_3DBox_list = box3D_object.Type3DBoxStruct.default_3DBox_list()

        win_name = 'mono_tracking'
        if self.show_images:
            cv2.namedWindow(str(win_name), cv2.WINDOW_NORMAL)
            cv2.resizeWindow(str(win_name), 1920, 1080)
            cv2.moveWindow(str(win_name), 1920, 0)

        # TODO: 对每个目标，计算其 mask 与 180/5=36 个航向角下 3D 包围盒的重叠率，选取最高的作为航向角.

        for frame_idx, (_, im) in enumerate(dataset):
            d_print_b(f'{frame_idx:4d} {im.shape}')
            results = model.detect([im], verbose=1)
            r = results[0]
            det_object_list = []

            # 在缩放的图像上进行航向角拟合
            im_1 = cv2.resize(im, None, fx=self.config.img_scale, fy=self.config.img_scale, interpolation = cv2.INTER_CUBIC)
            im_current_1 = copy.copy(im_1)
            im_size_1 = (im_1.shape[0], im_1.shape[1])
            array_inputs = []

            for det_id in range(0, len(r['rois'])):
                # 解析检测结果
                # Extract info
                det_2Dbox = np.array([r['rois'][det_id][0], r['rois'][det_id][1], r['rois'][det_id][2], r['rois'][det_id][3]], dtype= np.int16)
                det_2Dbox.shape = (4,1)

                confidence = r['scores'][det_id]

                label_id = r['class_ids'][det_id]
                label = class_names[label_id]

                det_mask = r['masks'][:,:,det_id]
                height = det_mask.shape[0]
                width = det_mask.shape[1]

                # Create det object
                det = DetObject(det_id, label, det_2Dbox, confidence,
                                       image_width = width, image_height = height,
                                       det_mask = det_mask,
                                       frame_name = f'frame-{frame_idx:04d}',
                                       frame_id = frame_idx)
                im = det.display_on_image(im)
                # det_object_list.append(det)
                for type_3DBox in type_3DBox_list:
                    if det.label ==  type_3DBox.label:
                        det_scaled = det.to_scale(self.config.img_scale, self.config.img_scale)
                        input_dict = {}
                        input_dict['mask'] = det_scaled.det_mask
                        input_dict['roi'] = det_scaled.det_2Dbox
                        input_dict['det_id'] = det_scaled.det_id
                        input_dict['cam_model'] = cam_model_1
                        input_dict['im_size'] =  im_size_1
                        input_dict['box_size'] = type_3DBox.box3D_lwh
                        array_inputs.append(input_dict)


            # Run the array of inputs through the pool of workers
            print("Thread alive: {}".format(threading.active_count()))
            not_done = True
            while(not_done):
                try:
                    results = pool.map(Box3D_utils.find_3Dbox_multithread, array_inputs)
                    not_done = False
                except Exception as e:
                    print(e)
                    not_done = True

            box3D_list = []
            for result in results:
                box3D_list.append(result['box_3D'])

            for result in results:
                # Get result:
                box3D_result = result['box_3D']
                mask_1 = result['mask']

                # Display box on image
                box3D_result.display_on_image(im_current_1, cam_model_1)

                mask_box_1 = box3D_result.create_mask(cam_model_1, im_size_1)

                o_1, mo_1, mo_1_b = Box3D_utils.overlap_mask(mask_1, mask_box_1)
                print("Overlap total: {}".format(o_1))

                # Do not plot the 3D box if overlap < 70 %
                if box3D_result.percent_overlap < 0.5:
                    im_current_1 = det_object.draw_mask(im_current_1, mask_box_1, (255,0,0))
                    im_current_1 = det_object.draw_mask(im_current_1, mask_1, (255,0,0))
                else:
                    im_current_1 = det_object.draw_mask(im_current_1, mask_box_1, (0,0,255))
                    im_current_1 = det_object.draw_mask(im_current_1, mask_1, (0,255,255))

            cv2.imwrite(osp.join(self.output_dir, f'frame-{frame_idx:04d}.jpg'), im)
            cv2.imwrite(osp.join(self.output_dir, f'yaw-frame-{frame_idx:04d}.jpg'), im_current_1)

            if self.show_images:
                cv2.imshow(str(win_name), im)
                if cv2.waitKey(30) == ord('q'):  # 1 millisecond
                    exit()


def main():
    parser = argparse.ArgumentParser(
        description='Realtime mono tracking with trajectory-extractor')
    parser.add_argument('-v', '--video_path', type=str,
                        default='test_alaco/sample/W91_2023-04-25_17_23_31.mp4',
                        help='input video path')
    parser.add_argument('--skip', type=int,
                        default=1,
                        help='Save one frame every skip frame')
    parser.add_argument('--max_frame', type=int,
                        default=5,
                        help='Only parse first max_frame frames')
    parser.add_argument('--frame_start', type=int,
                        default=0,
                        help='skip first frame_start frames')
    parser.add_argument('--show_images',
                        action ='store_true',
                        help='Show detections on images')
    parser.add_argument('--output_dir', type=str,
                        default='',
                        help='Path of the output')
    parser.add_argument('--camera_model', type=str,
                        default='test_alaco/alaco_cameras/10.10.145.231_cfg.yml',
                        help='Path to the camera model yaml')
    parser.add_argument('--img_scale', type = float,
                        default=0.2,
                        help='Image scaling factor to improve speed')
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

    mono = MonoTracking(args)
    mono.run()


if __name__ == "__main__":
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    main()

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
