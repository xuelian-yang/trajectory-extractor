########################################################################################
#
# Implementation of utils function for camera calibration
#
########################################################################################

import cv2
import numpy as np
import sys
import os.path as osp
import scipy.optimize as opt

from traj_ext.utils import mathutil

sys.path.append(osp.abspath(osp.join(osp.dirname(__file__), '../..')))
from common.util import *

def split(u, v, points):
    # return points on left side of UV
    return [p for p in points if np.cross(p[0:2] - u[0:2], v[0:2] - u[0:2]) < 0]

def extend(u, v, points):
    if not points:
        return []

    # find furthest point W, and split search to WV, UW
    w = min(points, key=lambda p: np.cross(p[0:2] - u[0:2], v[0:2] - u[0:2]))
    p1, p2 = split(w, v, points), split(u, w, points)
    return extend(w, v, p1) + [w] + extend(u, w, p2)

def convex_hull(points):
    # find two hull points, U, V, and split to left and right search
    u = min(points, key=lambda p: p[0])
    v = max(points, key=lambda p: p[0])
    left, right = split(u, v, points), split(v, u, points)

    # find convex hull on each side
    convex_full_list =  [v] + extend(u, v, left) + [u] + extend(v, u, right) + [v]
    return np.array(convex_full_list);

# Constraint function: Constraint the time to be positive
def func_cons(opti_params):
    focal_length = opti_params[0];
    return focal_length;


def func(opti_params, im_size, image_points, model_points_F, cam_name, enable_undistort):

    # Camera internals
    focal_length = opti_params[0]

    # Find camera parms
    rot_vec_CF_F, trans_CF_F, camera_matrix, dist_coeffs, image_points_reproj = find_camera_params(im_size, focal_length, image_points, model_points_F, cam_name, enable_undistort);

    # Compute error
    error_reproj = np.linalg.norm(np.subtract(image_points_reproj, image_points));

    return error_reproj;


def find_camera_params_opt(im_size, image_points, model_points_F, cam_name, enable_undistort, satellite_mode = False):

    # Pin-hole camera model: https://docs.opencv.org/2.4/modules/calib3d/doc/camera_calibration_and_3d_reconstruction.html
    # Important to understand the Pin-Hole camera model:
    # s*[px; py; 1] = camera_matrix*[rot_CF_F, trans_CF_F]*[pos_F;1];
    # px, py: pixel position
    # rot_CF_F: frame rotation matrix from Camera Frame to Model Frame
    # trans_CF_F: Position of the origin of the Model Frame expressed in the Camera Frame
    # camera_matrix: intrinsic camera parameters
    # satellite_mode: Set the focal length to be size_image/2 since there is an ambiguity between focal_length and Z position for top-down view


    # Start with a guess:
    p_init = [im_size[1]];

    # Impose a constraint on the focal lenght: It must be positive
    cons = ({'type': 'ineq', 'fun': lambda x : func_cons(x)});

    # If not in satellite mode, also estimate the focal_lenght
    if not (satellite_mode):
        # Run the optimization to find the optimal parameters
        param = opt.minimize(func, p_init, constraints=cons, args=(im_size, image_points, model_points_F, cam_name, enable_undistort))
        focal_length = param.x[0]

    # Set the focal_lenght in sattelite mode to avoid ambiguity in the optimization
    else:
        focal_length = (im_size[0]);

    # Find camera parms
    rot_vec_CF_F, trans_CF_F, camera_matrix, dist_coeffs, image_points_reproj = find_camera_params(im_size, focal_length, image_points, model_points_F, cam_name, enable_undistort)

    # Compute error
    error_reproj = np.linalg.norm(np.subtract(image_points_reproj, image_points));

    # Ouput results
    if False:
        print("Error Reproj:\n {0}".format(error_reproj));
        print("Camera Matrix:\n {0}".format(camera_matrix));
        print("Rotation Vector:\n {0}".format(rot_vec_CF_F));
        print("Translation Vector:\n {0}".format(trans_CF_F));

    return rot_vec_CF_F, trans_CF_F, camera_matrix, dist_coeffs, image_points_reproj;

def load_intrinsic_default(cam_name):
    """ 读取预标定好的相机内参
    由 ../gui_module/calib_core.py 生成
    """
    succ = True
    mtx, dist = None, None
    # 填充内参及畸变系数
    if cam_name == 'A_W_231':
        mtx = np.array(
            [[4.63200849e+03, 0.00000000e+00, 2.04417817e+03],
             [0.00000000e+00, 4.63270381e+03, 1.15794548e+03],
             [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]],
            dtype=np.float64)
        dist = np.array(
            [[-4.99835993e-01],  [7.80738347e-01],  [7.39888739e-04], [-4.47371462e-04], [-1.95261368e+00]],
            dtype=np.float64)

    elif cam_name == 'B_E_232':
        # 2023-09-18 采集的东向相机图像标定效果不太好 - 去畸变形状不太正常 - >> mean_dis: 6.759545894264592
        mtx = np.array(
            [[4.61387542e+03, 0.00000000e+00, 2.04260043e+03],
             [0.00000000e+00, 4.61293269e+03, 1.01555803e+03],
             [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]],
            dtype=np.float64)
        dist = np.array(
            [[-5.47785313e-01],  [1.21307520e+00], [2.00770261e-03], [-9.97803869e-04], [-3.15329884e+00]],
            dtype=np.float64)
        # 2023-10-11 对东向相机重新采集图像并标定 - >> mean_dis: 6.891272849933542
        mtx = np.array(
            [[4.6575934581539932e+03, 0., 2.0259661538013900e+03],
             [0., 4.6589345315260998e+03, 1.0128574735490064e+03],
             [0.0000000000e+00, 0.000000000e+00, 1.000000000e+00]],
            dtype=np.float64)
        dist = np.array(
            [[-5.4843891197182915e-01], [9.5865067385716807e-01], [1.1680107045556522e-03], [5.2066018814420493e-05], [-1.8090668401064214e+00]],
            dtype=np.float64)
        # 2023-10-11 + 2023-09-18 448 帧标定结果 - >> mean_dis: 6.857518885235537
        mtx = np.array(
            [[4.6521286399021010e+03, 0., 2.0300699745362722e+03],
             [0., 4.6529636757569060e+03, 1.0163649207688464e+03],
             [0., 0., 1.]],
            dtype=np.float64)
        dist = np.array(
            [[-5.4302430072019003e-01], [9.3195397621372433e-01], [1.1434760399876547e-03], [-2.1612530959566389e-04], [-1.7630518310827235e+00]],
            dtype=np.float64)

    elif cam_name == 'C_S_233':
        mtx = np.array(
            [[4.64681608e+03, 0.00000000e+00, 2.05671269e+03],
             [0.00000000e+00, 4.64880939e+03, 1.11499109e+03],
             [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]],
            dtype=np.float64)
        dist = np.array(
            [[-4.90232814e-01],  [6.80283772e-01],  [2.03555887e-04],  [1.48626632e-04], [-1.68401814e+00]],
            dtype=np.float64)
    elif cam_name == 'D_N_234':
        mtx = np.array(
            [[4.62872252e+03, 0.00000000e+00, 2.08329964e+03],
             [0.00000000e+00, 4.62912711e+03, 1.11627799e+03],
             [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]],
            dtype=np.float64)
        dist = np.array(
            [[-4.80737428e-01],  [6.19535464e-01], [-6.77668774e-05],  [4.40989113e-04], [-1.52697794e+00]],
            dtype=np.float64)
    else:
        succ = False
    return succ, mtx, dist

def find_camera_params(im_size, focal_length, image_points, model_points_F, cam_name, enable_undistort):

    # Pin-hole camera model: https://docs.opencv.org/2.4/modules/calib3d/doc/camera_calibration_and_3d_reconstruction.html
    # Important to understand the Pin-Hole camera model:
    # s*[px; py; 1] = camera_matrix*[rot_CF_F, trans_CF_F]*[pos_F;1];
    # px, py: pixel position
    # rot_CF_F: frame rotation matrix from Camera Frame to Model Frame
    # trans_CF_F: Position of the origin of the Model Frame expressed in the Camera Frame
    # camera_matrix: intrinsic camera parameters

    # Camera internals
    focal_length = focal_length
    center = (im_size[1]/2, im_size[0]/2)
    camera_matrix = np.array(
                             [[focal_length, 0, center[0]],
                             [0, focal_length, center[1]],
                             [0, 0, 1]], dtype = "double"
                             )

    # Assuming no lens distortion
    dist_coeffs = np.zeros((5, 1))
    if enable_undistort:
        # 使用预标定好的相机内参
        succ, mtx, dist = load_intrinsic_default(cam_name)
        if succ:
            camera_matrix = mtx
            dist_coeffs = dist

    # Use solvePnP to compute the camera rotation and position from the 2D - 3D point corespondance
    (success, rot_vec_CF_F, trans_CF_F) = cv2.solvePnP(model_points_F, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
    # d_print(f'\n===== solvePnP result =====', 'red')
    # d_print(f'  >> success: {success} @ [{__file__}:{line_no()}', 'yellow')

    # points_F_list = [];
    # for i in range(model_points_F.shape[0]):
    #     # print(model_points_F[i,:])
    #     # print(model_points_F.shape[0])
    #     points_F_list.append(model_points_F[i,:]);

    # points_px_list = [];
    # for i in range(image_points.shape[0]):
    #     # print(image_points[i,:])
    #     # print(image_points.shape[0])
    #     points_px_list.append(image_points[i,:]);

    # print(points_px_list)
    # ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera([np.float32([points_F_list])], [np.float32([points_px_list])], im_size,None,None)
    # print('mtx: {}'.format(mtx))
    # print('rvecs: {}'.format(rvecs))
    # print('tvecs: {}'.format(tvecs))

    # Reproject model_points_F on image plane according to determined params
    imagePoints, jacobian = cv2.projectPoints(model_points_F, rot_vec_CF_F, trans_CF_F, camera_matrix, dist_coeffs)
    image_points_reproj = imagePoints[:,0]

    return rot_vec_CF_F, trans_CF_F, camera_matrix, dist_coeffs, image_points_reproj;


def convert_latlon_F(latlon_origin, latlon_points):

    model_points_F = np.array([]);
    model_points_F.shape = (0,3);

    for latlon_p in latlon_points:
        ned = mathutil.latlon_to_NED(latlon_origin, latlon_p);
        # Force to Z = 0
        ned = np.append(ned, 0);
        ned.shape = (1,3);
        model_points_F = np.append(model_points_F, ned, axis=0);

    return model_points_F;

def display_keypoints(image, image_points_reproj, image_points):
    # 红色为原始点
    for i in range(0, image_points.shape[0]):
        cv2.circle(image, (int(image_points[i][0]), int(image_points[i][1])), 7, (0,0, 255), -1)

    # image_points_reproj 黄色为重投影点
    for i in range(0, image_points_reproj.shape[0]):
        cv2.circle(image, (int(image_points_reproj[i][0]), int(image_points_reproj[i][1])), 5, (0,255, 255), 2)

    # 计算重投影误差
    # d_print(f'>> image_points:        {image_points.dtype} {image_points.shape}')
    # d_print(f'>> image_points_reproj: {image_points_reproj.dtype} {image_points_reproj.shape}')
    err = np.linalg.norm(image_points_reproj - image_points)
    # d_print(f'{len(image_points)}')
    mean_err = np.sqrt(err ** 2 / len(image_points))
    d_print(f'>> mean_err: {mean_err} @ [{__file__}:{line_no()}', 'yellow')
    dis = np.linalg.norm(image_points_reproj - image_points, axis=1)
    mean_dis = np.average(dis)
    d_print(f'>> dis: {dis.shape} {dis.dtype}\n{dis}')
    d_print(f'>> mean_dis: {mean_dis}', 'red')

    return image, mean_dis