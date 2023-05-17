<!-- @created at 2023-05-12 -->

# Contents

- [Contents](#contents)
- [测试脚本](#测试脚本)
- [工具](#工具)
  - [视频分割](#视频分割)
  - [工具包](#工具包)

<!-- ========= ========= =========  ========= ========= -->

# 测试脚本

- 原论文的 demo:
  - Linux: run_trajectory_extraction.sh
  - Win10: run_trajectory_extraction.bat

- 标定单个相机:
  - Linux: run_calib.sh
  - Win10: run_alaco.bat

- 处理单个 alaco 视频:
  - Linux: run_alaco.sh
  - Win10: run_alaco.bat

- 处理多个 alaco 视频:
  - Linux: batch_run_alaco_videos.sh
  - Win10: batch_run_alaco_videos.bat

# 工具

## 视频分割

```bash
# 样例: scripts/split_video.sh
# 将视频 W91_2023-04-25_17_23_30.mp4 第 00:00:10 开始的 25 秒文件分割为 seg_25_sec.mp4
#   Windows 下 ffmpeg 使用完整路径, 如: E:/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe
ffmpeg -i W91_2023-04-25_17_23_30.mp4  -ss 10 -t 25 seg_25_sec.mp4
ffmpeg -i W91_2023-04-25_17_23_30.mp4  -ss 00:00:10 -t 00:00:25 seg_25_sec.mp4

ffmpeg -i W91_2023-04-25_17_23_30.mp4  -ss 1 -t 00:00:12 W91_2023-04-25_17_23_31.mp4
E:/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe -i W92_2023-04-25_17_23_30.mp4  -ss 1 -t 00:00:12 W92_2023-04-25_17_23_31.mp4

# 参考:
#   https://zhuanlan.zhihu.com/p/455572544
#     20个 FFmpeg操作命令
```

## 工具包

- [x] `traj_ext/box3D_fitting/run_optim_3Dbox_mono.py`
  - 通过最大化 3D 框与语义分割 mask 的重叠率来拟合目标的航向角

- [x] `traj_ext/camera_calib/run_calib_manual.py`
  - 提供特征点的像素坐标、经纬度进行相机内外参标定

- [x] `traj_ext/camera_calib/run_calib_stereo.py`
  - 已知 相机1 内外参，手动选取 相机1 与 相机2 间的至少 4 对关联点，实现 相机2 的标定

- [x] `traj_ext/camera_calib/run_detection_zone.py`
  - 在前视图上手动选取 ROI 凸包，同步生成俯视图上对应凸包

- [x] `traj_ext/camera_calib/run_show_calib.py`
  - 将 ROI 凸包叠加到图像上显示

- [x] `traj_ext/det_association/run_det_association.py`
  - 对 Mask_RCNN 输出的帧间目标进行关联匹配

- [x] `traj_ext/hd_map/run_generate_HD_map.py`
  - 交互式绘制图像上对应的道路元素: 车道线、停止线、道路边缘

- [ ] `traj_ext/object_det/run_create_det_object.py`

- [ ] `traj_ext/object_det/run_inspect_det.py`

- [x] `traj_ext/object_det/run_saveimages.py`
  - 从视频中解析图像并保存

- [x] `traj_ext/object_det/mask_rcnn/run_detections_csv.py`
  - 使用 Mask_RCNN 进行目标检测与分割

- [ ] `traj_ext/postprocess_track/run_postprocess.py`

- [ ] `traj_ext/utils/run_shrink_det_zone.py`

- [ ] `traj_ext/visualization/run_generate_meta.py`

- [ ] `traj_ext/visualization/run_inspect_traj.py`

- [x] `traj_ext/visualization/run_visualizer.py`
  - 在高精地图、原始图像上呈现检测结果 (ID、速度)

<!-- ========= ========= =========  ========= ========= -->

<!--
^
^
^
^
^
-->

<!-- ========= ========= =========  ========= ========= -->

<!-- ========= ========= =========  ========= ========= -->

<!--
- <div align="left"><img src="xxx" height="" width="640" /></div>

<details>
<summary>
</summary>
<br/>
</details>
-->

<!-- End of File -->
