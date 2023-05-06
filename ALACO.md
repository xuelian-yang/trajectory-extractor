<!-- @created at 2023-05-06 -->

# 目录

- [目录](#目录)
- [conda env @ ubuntu](#conda-env--ubuntu)
  - [conda env @ windows 10](#conda-env--windows-10)
- [生成 demo](#生成-demo)
  - [执行步骤](#执行步骤)
    - [遇到的问题](#遇到的问题)

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
python traj_ext/object_det/run_saveimages.py

# 2. OBJECT DETECTION
python traj_ext/object_det/mask_rcnn/run_detections_csv.py

# 3. VEHICLES
# 3.1 Det association
python traj_ext/det_association/run_det_association.py

# 3.2 Process
python traj_ext/postprocess_track/run_postprocess.py
python traj_ext/visualization/run_inspect_traj.py

# 4. PEDESTRIAN
# 4.1 Det association
python traj_ext/det_association/run_det_association.py

# 4.2 Process
python traj_ext/postprocess_track/run_postprocess.py
python traj_ext/visualization/run_inspect_traj.py

# 5. VISUALIZATION
python traj_ext/visualization/run_visualizer.py
```

### 遇到的问题

- [AttributeError: module 'keras.engine' has no attribute 'Layer'](https://stackoverflow.com/a/71260250)

  ```bash
  KE.Layer -> KL.Layer
  ```

- [Object Detection Using Mask R-CNN with TensorFlow 2.0 and Keras](https://blog.paperspace.com/mask-r-cnn-tensorflow-2-0-keras/)

- [ValueError: Tried to convert 'shape' to a tensor and failed. Error: None values not supported. #1070](https://github.com/matterport/Mask_RCNN/issues/1070)

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
