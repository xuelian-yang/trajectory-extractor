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

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '../..')))
from common.util import setup_log, d_print, get_name, d_print_b, d_print_g, d_print_r, d_print_y
from configs.workspace import WorkSpace

logger = logging.getLogger(__name__)
isWindows = (platform.system() == "Windows")


class LoadStreams:
    """
    References
    ----------
    yolov8_tracking/yolov8/ultralytics/yolo/data/dataloaders/stream_loaders.py
    """
    def __init__(self, sources, vid_stride=1):
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
            has_new_frame = False
            for i, cap in enumerate(self.caps):
                cap.grab()
                success, im = cap.retrieve()
                if success:
                    self.imgs[i] = im
                    self.num_frames[i] += 1
                    has_new_frame = True
                    if self.num_frames[i] % 50 == 0:
                        logging.info(f'  --> mp4 stream {i} cap {self.num_frames[i]:6d} frames {im.shape}')
                elif self.num_frames[i] >= self.frames[i] - 2:
                    logging.warning(f'stop iteration {self.count} with video [{i}]')
                    cap.release()
            if not has_new_frame:
                logging.warning(f'no new frame data, StopIteration {self.count}')
                cv2.destroyAllWindows()
                raise StopIteration
        return self.sources, im

    def __len__(self):
        return len(self.sources)  # 1E12 frames = 32 streams at 30 FPS for 30 years

class MonoTracking:
    def __init__(self, video_input, video_stride, save_dir):
        self.save_dir = save_dir
        self.video_input = video_input
        self.video_stride = video_stride

    def run(self):
        dataset = LoadStreams([self.video_input], self.video_stride)
        for frame_idx, batch in enumerate(dataset):
            d_print_b(f'{frame_idx:4d} ..')


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
                        default=500,
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

    mono = MonoTracking(args.video_path, args.skip, save_dir)
    mono.run()


if __name__ == "__main__":
    time_beg = time.time()
    this_filename = osp.basename(__file__)
    setup_log(this_filename)

    main()

    time_end = time.time()
    logger.warning(f'{this_filename} elapsed {time_end - time_beg} seconds')
    print(colored(f'{this_filename} elapsed {time_end - time_beg} seconds', 'yellow'))
