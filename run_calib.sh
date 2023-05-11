#!/bin/bash

time_sh_start=$(date +"%s.%N")

# ============================================================================ #
# < run clib >
# ============================================================================ #
# SET THE PATH AND CONFIG
alaco_temp_dir="temp/calib_feature_parser"
alaco_input_dir="test_alaco/hdmap_calib"
temp_path="temp"
json_ext=".json"
png_ext=".png"

png_name_cam="10.10.145.232"
feat_name_cam="feature_points_"${png_name_cam}
png_name_hd="hdmap_0"
feat_name_hd="feature_points_"${png_name_hd}

# ============================================================================ #
# Commands
# ============================================================================ #
# 注: 操作完不停地按 Enter 键保存

# 生成标定输入
python traj_ext/camera_calib/calib_feature_parser.py \
  --labelme_json ${feat_name_cam}${json_ext}

python traj_ext/camera_calib/calib_feature_parser.py \
  --labelme_json ${feat_name_hd}${json_ext}

# 标定
python traj_ext/camera_calib/run_calib_manual.py \
  -calib_points ${alaco_temp_dir}/${feat_name_cam}${json_ext}"_camera_calib_manual_latlon.csv" \
  -image ${alaco_input_dir}/${png_name_cam}${png_ext}

python traj_ext/camera_calib/run_calib_manual.py \
  -calib_points ${alaco_temp_dir}/${feat_name_hd}${json_ext}"_camera_calib_manual_latlon.csv" \
  -image ${alaco_input_dir}/${png_name_hd}${png_ext}


# 手动选取检测区域
python traj_ext/camera_calib/run_detection_zone.py \
  -camera_street ${temp_path}"/run_calib_manual/"${png_name_cam}"_cfg.yml" \
  -image_street ${alaco_input_dir}/${png_name_cam}${png_ext} \
  -camera_sat ${temp_path}"/run_calib_manual/"${png_name_hd}"_cfg.yml" \
  -image_sat ${alaco_input_dir}/${png_name_hd}${png_ext} \
  -output_name ${png_name_cam}


# 显示 ROI 区域
python traj_ext/camera_calib/run_show_calib.py \
  --camera_calib ${temp_path}"/run_calib_manual/"${png_name_cam}"_cfg.yml" \
  --image ${alaco_input_dir}/${png_name_cam}${png_ext} \
  --detection_zone ${temp_path}"/run_detection_zone/"${png_name_cam}"_detection_zone.yml"

# ============================================================================ #
# </run calib >
# ============================================================================ #

function text_warn() {
  echo -e "\e[33m# $1\e[39m"
}

time_sh_end=$(date +"%s.%N")
time_diff_sh=$(bc <<< "$time_sh_end - $time_sh_start")
text_warn "run_calib.sh elapsed:  $time_diff_sh   seconds. ($time_sh_end - $time_sh_start)"
