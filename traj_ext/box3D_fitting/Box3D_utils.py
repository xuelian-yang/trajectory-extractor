# -*- coding: utf-8 -*-
# @Author: Aubrey
# @Date:   2018-07-24 10:44:20
# @Last Modified by:   Aubrey
# @Email: clausse.aubrey@gmail.com
# @Github:


###################################################################################
#
# 3DBox_utils.py defines usefull functions to compute the 3D position
# of an object from its mask.
#
###################################################################################

import logging
import numpy as np
import cv2
import sys
import scipy.optimize as opt
import threading

from traj_ext.utils.mathutil import *

from traj_ext.box3D_fitting import box3D_object

import os.path as osp
import sys
sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '..')))
from common.util import itti_traceback

#@itti_traceback
def overlap_mask(mask_1, mask_2):
    """Compute overlapping score.
       Weight more the regions of mask_1 going out of the region of mask_2 in count.
    计算 mask 间重叠比例
    Args:
        mask_1 (TYPE): Mask 1
        mask_2 (TYPE): Mask 2

    Returns:
        TYPE: count, mask_count_1, mask_count_2;
    """

    # Overlap Mask
    overlap_mask = np.logical_and(mask_1 == 1, mask_2 == 1)  # 交集 mask_1 & mask_2

    # Mask of region: Mask_i \ Overlap
    mask_count_1 = (np.logical_and(mask_1 == 1, overlap_mask == 0))  # 补集 mask_1 & (~ mask_2)
    mask_count_2 = (np.logical_and(mask_2 == 1, overlap_mask == 0))  # 补集 mask_2 & (~ mask_1)

    # Count the 1
    count_1 =  np.count_nonzero(mask_count_1)  # mask_1 在交集外的像素数量
    count_2 =  np.count_nonzero(mask_count_2)  # mask_2 在交集外的像素数量

    # Weight more the regions of mask_1 going out of the region of mask_2 (e.g we want mask_1 to be inside mask_2)
    count =  4*count_1 + count_2  # 加权计算

    return count, mask_count_1, mask_count_2;

#@itti_traceback
def compute_cost_mono(opti_params, im_size, cam_model, mask, param_fix):
    """Compute the overlap cost for mono image between
    计算 3D 包围盒与图像分割 mask 间重叠率.
    Args:
        opti_params (TYPE): Description
        im_size (TYPE): Description
        cam_model (TYPE): Description
        mask (TYPE): Description
        param_fix (TYPE): Description

    Returns:
        TYPE: Overlap score
    """

    # Get optim paramters
    psi_rad = opti_params[0];
    x = opti_params[1];
    y = opti_params[2];

    # Get fixed paramters
    z = param_fix[0];
    l = param_fix[1];
    w = param_fix[2];
    h = param_fix[3];

    # Create 3D box corners points
    box3D = box3D_object.Box3DObject(psi_rad, x, y, z, l, w, h);

    # Mask box
    mask_3Dbox = box3D.create_mask(cam_model, im_size)  # 转为图像上的凸包

    # Compute overlap score
    overlap_score, masko_1, masko_2 = overlap_mask(mask, mask_3Dbox);

    # Return overlap_score
    return overlap_score;

#@itti_traceback
def overlap_percentage_mask(mask_1, mask_2):
    """Compute overlapping percentage between two masks: Intersection over Union

    Args:
        mask_1 (TYPE): Mask 1
        mask_2 (TYPE): Mask 2

    Returns:
        TYPE: Percent overlap
    """
    # Overlap Mask
    overlap_mask = np.logical_and(mask_1, mask_2);

    # Union mask
    union_mask = np.logical_or(mask_1, mask_2);

    # Count the 1
    count_overlap =  np.count_nonzero(overlap_mask);
    count_union =  np.count_nonzero(union_mask);

    # Weight more the regions of mask_1 going out of the region of mask_2 (e.g we want mask_1 to be inside mask_2)
    percent_overlap =  float(count_overlap) / float(count_union);

    return percent_overlap;

#@itti_traceback
def compute_cost_stero(opti_params, im_size_1, im_size_2, cam_model_1, cam_model_2, mask_1, mask_2,param_fix):
    """Compute the overlap cost for steareo images between.
    Cost is the sum of the cost on each image (but one position / orientation in 3D of the 3DBox)

    Args:
        opti_params (TYPE): Description
        im_size_1 (TYPE): Description
        im_size_2 (TYPE): Description
        cam_model_1 (TYPE): Description
        cam_model_2 (TYPE): Description
        mask_1 (TYPE): Description
        mask_2 (TYPE): Description
        param_fix (TYPE): Description

    Returns:
        TYPE: Total cost
    """

    # Compute cost for each image:
    cost_1 = compute_cost_mono(opti_params, im_size_1, cam_model_1, mask_1, param_fix);
    cost_2 = compute_cost_mono(opti_params, im_size_2, cam_model_2, mask_2, param_fix)

    # Sum the cost:
    total_cost = cost_1 + cost_2;

    # Return total_cost
    return total_cost;

#@itti_traceback
def find_3Dbox(mask, roi, cam_model, im_size, box_size_lwh):
    """Find 3D box correspondig to a mask
    此接口非常慢: (720, 1280, 3) 降采样到 (144, 256, 3) 后, 单个框的拟合耗时可达 3.5 秒
    Args:
        mask (TYPE): Mask
        roi (TYPE): Region of interest
        cam_model (TYPE): Camera model
        im_size (TYPE): Size of the image (tulpe)
        box_size_lwh (TYPE): Box size: length, width, height in meters

    Returns:
        TYPE: box3D object
    """
    # mask: bool array of the size of the image
    # roi: corner coordinates of the ROI (2D bounding box) of the detected object
    # cam_model: camera model
    # im_size: Image size
    # box_size_lwh: 3D box size [length, width, height]

    # Get ROI coordinates
    x_1 = int(roi[1]);
    y_1 = int(roi[0]);
    x_2 = int(roi[3]);
    y_2 = int(roi[2]);

    tl = (x_1, y_1)
    br = (x_2, y_2)

    # Compute rough 3D position of the object:
    # Re-project the center of the ROI on the ground

    # Get center of ROI
    pt_image_x = (x_1 + x_2)/2
    pt_image_y = (y_1 + y_2)/2

    # 3D position by re-projection on the ground
    pt_image = (int(pt_image_x), int(pt_image_y));
    pos_FNED_init = cam_model.projection_ground(0, pt_image);
    pos_FNED_init.shape = (1,3);

    # Construct initial 3D box:
    psi_rad = float(0.0);            # Orientation of the box (yaw) - rad
    x = float(pos_FNED_init[0,0]);   # Position X in F_NED of the center of the bottom side (defined implicitly by the camera paramters) - meters
    y = float(pos_FNED_init[0,1]);   # Position Y in F_NED of the center of the bottom side (defined implicitly by the camera paramters) - meters
    z = float(0.0);                  # Position Z in F_NED of the center of the bottom side (defined implicitly by the camera paramters) - meters
    l = float(box_size_lwh[0]);          # Length of the 3D Box - meters
    w = float(box_size_lwh[1]);          # Width of the 3D Box - meters
    h = float(box_size_lwh[2]);          # Height of the 3D Box - meters

    # Run the optimization with different Initial Guess
    # Allow to avoid getting stuck on local optimum
    # Especially on the orientation (yaw), as the optimizer has a hard time find good orientation
    param_min = None;
    for psi_deg in range(0,180,60):

        psi_rad = np.deg2rad(psi_deg);

        # We only optimize Yaw, Position X, Position Y
        param_opt = [psi_rad, x, y];

        # Position Z assume to be 0
        # 3DBox size: Defined by the class ID
        param_fix = [z, l, w, h];
        p_init = param_opt;

        # Run optimizer: Good method: COBYLA, Powell - 基于最大化重叠率拟合航向角
        param = opt.minimize(compute_cost_mono, p_init, method='Powell', args=(im_size, cam_model, mask, param_fix), options={'maxfev': 1000, 'disp': True});
        if param_min is None:
            param_min = param;

        # Keep the best values among the different run with different initial guesses
        if param.fun < param_min.fun:
            param_min = param;

    param = param_min;

    # Retrieve 3D box parameters:
    psi_rad = round(param.x[0],4);
    x = round(param.x[1],4);
    y = round(param.x[2],4);

    z = round(param_fix[0],4);
    l = round(param_fix[1],4);
    w = round(param_fix[2],4);
    h = round(param_fix[3],4);

    # Construct param_3Dbox
    box3D = box3D_object.Box3DObject(psi_rad, x, y, z, l, w, h);

    return box3D;

#@itti_traceback
def find_3Dbox_ex(mask, roi, cam_model, im_size, box_size_lwh):
    """
    对 find_3Dbox(..) 进行加速, 18
    """
    x_1, y_1 = int(roi[1]), int(roi[0])
    x_2, y_2 = int(roi[3]), int(roi[2])
    tl = (x_1, y_1)
    br = (x_2, y_2)

    # Get center of ROI
    pt_image_x = (x_1 + x_2)/2
    pt_image_y = (y_1 + y_2)/2

    # 3D position by re-projection on the ground
    pt_image = (int(pt_image_x), int(pt_image_y))
    pos_FNED_init = cam_model.projection_ground(0, pt_image)
    pos_FNED_init.shape = (1,3)

    # Construct initial 3D box:
    psi_rad = float(0.0)
    x = float(pos_FNED_init[0,0])
    y = float(pos_FNED_init[0,1])
    z = float(0.0)
    l = float(box_size_lwh[0])
    w = float(box_size_lwh[1])
    h = float(box_size_lwh[2])
    param_min = None
    init_x, init_y = x, y
    succ = 0
    use_minimize_method = True  # 使用 最优化方法还是线性搜索
    if use_minimize_method:
        for psi_deg in range(0,180,60):
            psi_rad = np.deg2rad(psi_deg)

            # We only optimize Yaw, Position X, Position Y
            param_opt = [psi_rad, x, y]

            # Position Z assume to be 0
            # 3DBox size: Defined by the class ID
            param_fix = [z, l, w, h]
            p_init = param_opt

            logging.info(f'({threading.get_ident()} / {threading.active_count()}) psi_deg: {psi_deg}, psi_rad: {psi_rad}, x: {x}, y: {y}')

            # Run optimizer: Good method: COBYLA, Powell - 基于最大化重叠率拟合航向角，最大迭代次数 maxfev 降为 100 次时，时间减半，效果差异不大
            # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
            param = opt.minimize(compute_cost_mono, p_init, method='Powell', args=(im_size, cam_model, mask, param_fix), options={'maxfev': 1000, 'disp': False})
            if param_min is None:
                succ += 1
                logging.info(f'({threading.get_ident()} / {threading.active_count()}), iter={succ} param=({param.x} {param.fun} {param.success})')
                param_min = param

            # Keep the best values among the different run with different initial guesses
            if param.fun < param_min.fun:
                succ += 1
                logging.info(f'({threading.get_ident()} / {threading.active_count()}), iter={succ} param=({param.x} {param.fun} {param.success})')
                param_min = param

        param = param_min
        logging.info(f'({threading.get_ident()} / {threading.active_count()}), final_iter={succ} param=({param.x} {param.fun} {param.success})')

        # Retrieve 3D box parameters:
        psi_rad = round(param.x[0],4)
        x = round(param.x[1],4)
        y = round(param.x[2],4)

        logging.warning(f'({threading.get_ident()} / {threading.active_count()}) Powell optimizer >>> yaw = {psi_rad}, x: {init_x} => {x}, y: {init_y} => {y}')

        z = round(param_fix[0],4)
        l = round(param_fix[1],4)
        w = round(param_fix[2],4)
        h = round(param_fix[3],4)

    else:  # 线性搜索
        best_psi_rad = None
        best_func = None
        for psi_deg in range(0, 180, 10):
            psi_rad = np.deg2rad(psi_deg)
            box3D = box3D_object.Box3DObject(psi_rad, x, y, z, l, w, h)
            mask_3Dbox = box3D.create_mask(cam_model, im_size)
            overlap_score, masko_1, masko_2 = overlap_mask(mask, mask_3Dbox)
            if best_func is None:
                best_func = overlap_score
                best_psi_rad = psi_rad
            elif best_func > overlap_score:
                best_func = overlap_score
                best_psi_rad = psi_rad
        psi_rad = best_psi_rad

    # Construct param_3Dbox
    box3D = box3D_object.Box3DObject(psi_rad, x, y, z, l, w, h)

    return box3D

#@itti_traceback
def find_3Dbox_multithread(input_dict):
    """Find 3D box correspondig to a mask. Adapted for a mutlithread pool input format (one dict)

    Args:
        input_dict (TYPE): Input dict with: mask, roi, cam_model, im_size, box_size

    Returns:
        TYPE: Description
    """
    logging.debug(f'find_3Dbox_multithread( {type(input_dict)}\n{input_dict["mask"].shape}\n{input_dict}')

    # Extract objetc from input_dict:
    mask = input_dict['mask'];
    roi =  input_dict['roi'];
    cam_model = input_dict['cam_model'];
    im_size = input_dict['im_size'];
    box_size_lwh = input_dict['box_size'];

    # Compute the 3D box:
    import time
    __time_beg = time.time()
    # box3D = find_3Dbox(mask, roi, cam_model, im_size, box_size_lwh);
    box3D = find_3Dbox_ex(mask, roi, cam_model, im_size, box_size_lwh)
    __time_end = time.time()
    logging.warning(f'find_3Dbox: {__time_end - __time_beg:.6f} seconds')
    box3D.set_det_id(input_dict['det_id']);

    # COmpute percentage overlap
    mask_box3D = box3D.create_mask(cam_model, im_size);
    percent_overlap = overlap_percentage_mask(mask_box3D, mask);
    box3D.set_percent_overlap(percent_overlap);

    # Construct result dict:
    result = {};
    result['box_3D'] = box3D;
    result['mask'] = mask;

    # Return result
    return result;
