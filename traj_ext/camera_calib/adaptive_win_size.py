# -*- coding: utf-8 -*-

# @File        :   adaptive_win_size.py
# @Description :   根据图像大小进行自适应缩放，以适应显示器分辨率
# @Time        :   2023/10/07 10:01:41
# @Author      :   Xuelian.Yang
# @Contact     :   Xuelian.Yang@geely.com

# here put the import lib
import sys
import os.path as osp

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '../..')))
from common.util import *

__all__ = ['find_scale']

def find_scale(img, n_win=1):
    """ 根据图像大小、窗口数量及预设的显示器分辨率查找缩放系数 """
    assert n_win == 1 or n_win == 2
    im_h, im_w, _ = img.shape
    screen_h, screen_w = 1080, 1920  # 显示器分辨率大小
    scale_h = (im_h * 1.0) / screen_h
    scale_w = (im_w * 1.0) / screen_w
    scale = max(scale_h, scale_w)
    scale_int = int(scale + 0.99 + 0.5)
    if n_win > 1:
        scale_int *= 2  # 需显示多个窗口

    # d_print(f'>> img: {img.shape}, n_win: {n_win}', 'green')
    # d_print(f'  >> scale_h:   {scale_h}')
    # d_print(f'  >> scale_w:   {scale_w}')
    # d_print(f'  >> scale:     {scale}', 'yellow')
    # d_print(f'  >> scale_int: {scale_int}', 'red')

    return scale_int
