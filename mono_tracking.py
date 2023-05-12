# -*- encoding: utf-8 -*-

# @File        :   mono_tracking.py
# @Description :   单目跟踪
# @Time        :   2023/05/12 13:51:37
# @Author      :   Xuelian.Yang
# @Contact     :   Xuelian.Yang@geely.com
# @LastEditors :   Xuelian.Yang
# @Example     :   python mono_tracking.py

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
import numpy as np
import os
import os.path as osp
import pandas as pd
import platform
import sys
from termcolor import colored
from threading import Thread
import time

FILE_PATH = osp.abspath(osp.dirname(__file__))
sys.path.append(osp.join(FILE_PATH, '../..'))
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
    def __init__(self, video_input, video_stride, max_frame, save_dir):
        self.save_dir = save_dir
        self.video_input = video_input
        self.video_stride = video_stride
        self.max_frame = max_frame
        self.display = False

    def run(self):
        dataset = LoadStreams([self.video_input], self.video_stride, self.max_frame)
        model = load_model()

        win_name = 'mono_tracking'
        if self.display:
            cv2.namedWindow(str(win_name), cv2.WINDOW_NORMAL)
            cv2.resizeWindow(str(win_name), 1920, 1080)
            cv2.moveWindow(str(win_name), 1920, 0)

        for frame_idx, (_, im) in enumerate(dataset):
            d_print_b(f'{frame_idx:4d} {im.shape}')
            results = model.detect([im], verbose=1)
            r = results[0]
            det_object_list = []
            for det_id in range(0,len(r['rois'])):

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
                det_object = DetObject(det_id, label, det_2Dbox, confidence,
                                       image_width = width, image_height = height,
                                       det_mask = det_mask,
                                       frame_name = f'frame-{frame_idx:04d}',
                                       frame_id = frame_idx)
                im = det_object.display_on_image(im)
                # det_object_list.append(det_object)
                cv2.imwrite(osp.join(self.save_dir, f'frame-{frame_idx:04d}.jpg'), im)
            if self.display:
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
    parser.add_argument('--max_frame_num', type=int,
                        default=5,
                        help='Only parse first max_frame_num frames')
    parser.add_argument('--frame_start', type=int,
                        default=0,
                        help='skip first frame_start frames')
    args = parser.parse_args()


    for item in vars(args):
        logger.info(f'{item:20s} : {getattr(args, item)}')

    ws = WorkSpace()
    save_dir = osp.join(ws.get_temp_dir(), get_name(__file__))
    if not osp.exists(save_dir):
        os.makedirs(save_dir)

    mono = MonoTracking(args.video_path, args.skip, args.max_frame_num, save_dir)
    mono.run()


if __name__ == "__main__":
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    main()

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
