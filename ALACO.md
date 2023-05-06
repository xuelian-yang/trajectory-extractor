<!-- @created at 2023-05-06 -->

# 目录

- [目录](#目录)
- [conda env](#conda-env)
- [生成 demo](#生成-demo)
  - [执行步骤](#执行步骤)
    - [遇到的问题](#遇到的问题)

<!-- ========= ========= =========  ========= ========= ========= -->

# conda env

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
