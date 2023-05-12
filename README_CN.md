<!-- @created at 2023-05-12 -->

# Contents

- [Contents](#contents)
- [测试脚本](#测试脚本)
- [工具](#工具)
  - [视频分割](#视频分割)

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
