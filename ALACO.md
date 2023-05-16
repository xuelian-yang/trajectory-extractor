<!-- @created at 2023-05-06 -->

# 目录

- [目录](#目录)
- [conda env @ ubuntu](#conda-env--ubuntu)
  - [conda env @ windows 10](#conda-env--windows-10)
- [生成 demo](#生成-demo)
  - [执行步骤](#执行步骤)
    - [遇到的问题](#遇到的问题)
      - [@Linux](#linux)
      - [@Win10](#win10)
- [工具](#工具)
  - [3D 框拟合](#3d-框拟合)

<!-- ========= ========= =========  ========= ========= ========= -->

# conda env @ ubuntu

```bash
conda create -n trajectory-extrator --clone dev
pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 安装 tensorflow-gpu
#   https://www.tensorflow.org/install/pip
nvidia-smi
#   CUDA Version: 11.6
conda install -c conda-forge cudatoolkit=11.6.0
pip install nvidia-cudnn-cu11==8.6.0.163 -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# Configure the system paths. You can do it with the following command every time you start a new terminal after activating your conda environment.
CUDNN_PATH=$(dirname $(python -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/:$CUDNN_PATH/lib

pip install --upgrade pip -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
pip install tensorflow==2.12.0 -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# For your convenience it is recommended that you automate it with the following commands. The system paths will be automatically configured when you activate this conda environment.
mkdir -p $CONDA_PREFIX/etc/conda/activate.d
echo 'CUDNN_PATH=$(dirname $(python -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))' >> $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/:$CUDNN_PATH/lib' >> $CONDA_PREFIX/etc/conda/activate.d/env_vars.sh

# Verify install
#   Verify the CPU setup:
python -c "import tensorflow as tf; print(tf.reduce_sum(tf.random.normal([1000, 1000])))"
#   Verify the GPU setup:
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

## conda env @ windows 10

```bash
# https://tensorflow.google.cn/install/pip#windows-native
conda install -c conda-forge cudatoolkit=11.2 cudnn=8.1.0

# Anything above 2.10 is not supported on the GPU on Windows Native
python -m pip install "tensorflow<2.11"
# Verify install:
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

# 生成 demo

```bash
conda activate trajectory-extrator
bash run_trajectory_extraction.sh
```

## 执行步骤

```bash
# 1. EXTRACTING FRAMES FROM VIDEO
python traj_ext/object_det/run_saveimages.py ^
  test_alaco/alaco_W92_2023-05-09_14_18_54/W92_2023-05-09_14_18_54.mp4 ^
  -skip 3

# 2. OBJECT DETECTION
python traj_ext/object_det/mask_rcnn/run_detections_csv.py ^
  -image_dir test_alaco/alaco_W92_2023-05-09_14_18_54/img ^
  -output_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output ^
  -crop_x1y1x2y2 [0, 0, 4096, 2160] ^
  -no_save_images

# 3. VEHICLES - 参数参考 PEDESTRIAN
# 3.1 Det association
python traj_ext/det_association/run_det_association.py

# 3.2 Process
python traj_ext/postprocess_track/run_postprocess.py
python traj_ext/visualization/run_inspect_traj.py

# 4. PEDESTRIAN
# 4.1 Det association
python traj_ext/det_association/run_det_association.py ^
  -image_dir test_alaco/alaco_W92_2023-05-09_14_18_54/img ^
  -output_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/pedestrians ^
  -det_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/det/csv ^
  -ignore_detection_area test_alaco/alaco_W92_2023-05-09_14_18_54/ ^
  -det_zone_im test_alaco/alaco_W92_2023-05-09_14_18_54/10.10.145.232_detection_zone_im.yml ^
  -mode pedestrians ^
  -no_save_images


# 4.2 Process
python traj_ext/postprocess_track/run_postprocess.py ^
  -image_dir test_alaco/alaco_W92_2023-05-09_14_18_54/img ^
  -output_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/pedestrians ^
  -det_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/det/csv ^
  -det_asso_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/pedestrians/det_association/csv ^
  -track_merge test_alaco/alaco_W92_2023-05-09_14_18_54/output/pedestrians/det_association/W92_2023-05-09_14_18_54_tracks_merge.csv ^
  -camera_street test_alaco/alaco_W92_2023-05-09_14_18_54/10.10.145.232_cfg.yml ^
  -camera_sat test_alaco/alaco_W92_2023-05-09_14_18_54/hdmap_0_cfg.yml ^
  -camera_sat_img test_alaco/alaco_W92_2023-05-09_14_18_54/hdmap_0.png ^
  -det_zone_fned test_alaco/alaco_W92_2023-05-09_14_18_54/10.10.145.232_detection_zone.yml ^
  -delta_ms 100 ^
  -location_name alaco_W92 ^
  -dynamic_model CV ^
  -date 20230509 ^
  -start_time 1418 ^
  -no_save_images

python traj_ext/visualization/run_inspect_traj.py ^
  -traj test_alaco/alaco_W92_2023-05-09_14_18_54/output/pedestrians/traj/csv/W92_2023-05-09_14_18_54_traj.csv ^
  -image_dir test_alaco/alaco_W92_2023-05-09_14_18_54/img ^
  -det_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/det/csv ^
  -det_asso_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/pedestrians/det_association/csv ^
  -track_merge test_alaco/alaco_W92_2023-05-09_14_18_54/output/pedestrians/det_association/W92_2023-05-09_14_18_54_tracks_merge.csv ^
  -camera_street test_alaco/alaco_W92_2023-05-09_14_18_54/10.10.145.232_cfg.yml ^
  -camera_sat test_alaco/alaco_W92_2023-05-09_14_18_54/hdmap_0_cfg.yml ^
  -camera_sat_img test_alaco/alaco_W92_2023-05-09_14_18_54/hdmap_0.png ^
  -det_zone_fned test_alaco/alaco_W92_2023-05-09_14_18_54/10.10.145.232_detection_zone.yml ^
  -label_replace person ^
  -output_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/pedestrians ^
  -hd_map test_alaco/alaco_W92_2023-05-09_14_18_54/hdmap_0_hd_map.csv ^
  -delta_ms 100 ^
  -location_name alaco_W92 ^
  -date 20230509 ^
  -start_time 1418 ^
  -export

# 5. VISUALIZATION
python traj_ext/visualization/run_visualizer.py ^
  -traj test_alaco/alaco_W92_2023-05-09_14_18_54/output/vehicles/traj_inspect/csv/W92_2023-05-09_14_18_54_traj.csv ^
  -traj_person test_alaco/alaco_W92_2023-05-09_14_18_54/output/pedestrians/traj_inspect/csv/W92_2023-05-09_14_18_54_traj.csv ^
  -image_dir test_alaco/alaco_W92_2023-05-09_14_18_54/img ^
  -camera_street test_alaco/alaco_W92_2023-05-09_14_18_54/10.10.145.232_cfg.yml ^
  -camera_sat test_alaco/alaco_W92_2023-05-09_14_18_54/hdmap_0_cfg.yml ^
  -camera_sat_img test_alaco/alaco_W92_2023-05-09_14_18_54/hdmap_0.png ^
  -det_zone_fned test_alaco/alaco_W92_2023-05-09_14_18_54/10.10.145.232_detection_zone.yml ^
  -hd_map test_alaco/alaco_W92_2023-05-09_14_18_54/hdmap_0_hd_map.csv ^
  -output_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output ^
  -export 1

# 6. Image Sequences to gif
python util_create_gif.py ^
  -img_seq_dir test_alaco/alaco_W92_2023-05-09_14_18_54/output/visualizer/img_concat ^
  -gif_name alaco_traj_demo_alaco_W92_2023-05-09_14_18_54_.gif
```

### 遇到的问题

#### @Linux

- [AttributeError: module 'keras.engine' has no attribute 'Layer'](https://stackoverflow.com/a/71260250)

  ```bash
  KE.Layer -> KL.Layer
  ```

- [Object Detection Using Mask R-CNN with TensorFlow 2.0 and Keras](https://blog.paperspace.com/mask-r-cnn-tensorflow-2-0-keras/)

- [ValueError: Tried to convert 'shape' to a tensor and failed. Error: None values not supported. #1070](https://github.com/matterport/Mask_RCNN/issues/1070)

#### @Win10

- [CondaHTTPError: HTTP 000 CONNECTION](https://zhuanlan.zhihu.com/p/260034241)

  ```bash
  # Windows 10 下为安装 tensorflow-gpu 运行 conda install -c conda-forge cudatoolkit=11.6.0 报错
  #   -> 关闭 clash
  #   -> 修改 C:\Users\Username\.condarc
  #      https:// -> http://
  #      ssl_verify: false
  ```

```bash
channels:
  - http://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
  - http://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
  - http://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/msys2/
  - http://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/bioconda/
  - http://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
  - http://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/fastai/
  - http://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch/
show_channel_urls: true
ssl_verify: false
```

- [res = cv2.pointPolygonTest(contour, pt, False)](https://blog.csdn.net/HayPinF/article/details/118000913)

```bash
    res = cv2.pointPolygonTest(contour, pt, False)

cv2.error: OpenCV(4.7.0) D:\a\opencv-python\opencv-python\opencv\modules\imgproc\src\geometry.cpp:103: error: (-215:Assertion failed) total >= 0 && (depth == CV_32S || depth == CV_32F) in function 'cv::pointPolygonTest'

res = cv2.pointPolygonTest(contour, pt, False)
==>
res = cv2.pointPolygonTest(np.array(contour, np.float32), pt, False)
```

- [AttributeError: module 'cv2' has no attribute 'TrackerCSRT_create'](https://blog.csdn.net/qq_18502653/article/details/98450073)

  ```bash
  # 需要安装 opencv-contrib-python
  #  实际已安装
  #     opencv-contrib-python  4.7.0.72
  #     opencv-python          4.7.0.72
  # Win10 与 ubuntu20.04 下安装的版本都一样，但仅有 Win10 报错.
  ```

# 工具

## 3D 框拟合

- Box3DObject

  ```python
  # traj_ext/box3D_fitting/box3D_object.py
  # ( 航向角、底面中心点坐标、长宽高、遮挡率、检测ID )
  self.psi_rad = psi_rad
  self.x = x
  self.y = y
  self.z = z
  self.length = length
  self.width = width
  self.height = height

  self.percent_overlap = percent_overlap  # Use for estimating 3D box from 2D mask
  self.det_id = det_id
  ```

- 预设的机非人3D框对应长宽高

  ```bash
  # traj_ext/box3D_fitting/box3D_object.py
  #     def default_3DBox_list(cls)
  # traj_ext/box3D_fitting/test/optim_3Dbox_mono_type_test.csv
  label,length,width,height
  car,4.0,1.8,1.6
  bus,12.0,2.6,2.5
  truck,6.0,2.4,2.0
  person,0.8,0.8,1.6
  motorcycle,1.2,0.8,1.6
  bicycle,1.2,0.8,1.6
  ```

<!-- ========= ========= =========  ========= ========= ========= -->

<!--
- <div align="left"><img src="xxx" height="" width="640" /></div>
<details>
<summary>
</summary>
<br/>
</details>
-->

<!-- End of File -->
