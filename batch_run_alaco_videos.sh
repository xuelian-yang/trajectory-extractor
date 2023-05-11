#!/bin/bash

time_sh_start=$(date +"%s.%N")

function text_warn() {
  echo -e "\e[33m# $1\e[39m"
}

# ============================================================================ #
# < batch run alaco videos >
# ============================================================================ #

# ============================================================================ #
# 处理单个视频
# ============================================================================ #
function alaco_video_demo() {
  var_video_dir=$1
  var_video_name=$2

  var_camera_name=${var_video_name:0:3}

  echo ">> ${var_video_dir}"
  echo ">> ${var_video_name}"
  echo ">> ${var_camera_name}"

  # 获取相机编码对应的 IP
  if [ ${var_camera_name} = "W91" ]; then
    var_camera_ip="10.10.145.231"
  elif [ ${var_camera_name} = "W92" ]; then
    var_camera_ip="10.10.145.232"
  elif [ ${var_camera_name} = "W93" ]; then
    var_camera_ip="10.10.145.233"
  elif [ ${var_camera_name} = "W94" ]; then
    var_camera_ip="10.10.145.234"
  else
    text_warn "unknown camera name ${var_camera_name}"
    return
  fi

  text_warn "IP of ${var_camera_name} is ${var_camera_ip}"

  # ALACO Demo 参数
  CASE_NAME="alaco_cameras"
  SOURCE_FOLDER="test_alaco/"${CASE_NAME}
  VIDEO_NAME=${var_video_dir}/${var_video_name}".mp4"
  NAME=${var_video_name}

  GIF_NAME="alaco_traj_demo_"${var_camera_ip}"_"${CASE_NAME}"_"${var_video_name}".gif"
  DELTA_MS=100
  LOCATION_NAME="alaco_"${var_camera_name}
  DATE="20230509"
  START_TIME="1418"

  # 标定文件
  CAMERA_STREET=${var_camera_ip}"_cfg.yml"
  CAMERA_SAT="hdmap_0_cfg.yml"
  CAMERA_SAT_IMG="hdmap_0.png"
  # 需要生成高精地图
  HD_MAP="hdmap_0_hd_map.csv"

  # DETECTION AD IGNORE ZONES
  DET_ZONE_IM_VEHICLES=${var_camera_ip}"_detection_zone_im.yml"
  DET_ZONE_FNED_VEHICLES=${var_camera_ip}"_detection_zone.yml"
  IGNORE_AREA_VEHICLES=""

  DET_ZONE_IM_PEDESTRIANS=${var_camera_ip}"_detection_zone_im.yml"
  DET_ZONE_FNED_PEDESTRIANS=${var_camera_ip}"_detection_zone.yml"
  # TODO: 生成行人忽略区域
  IGNORE_AREA_PEDESTRIANS=""

  # CROP VALUES FOR DETECTION HERE IF NEEDED
  # TODO: 设置裁剪区域
  CROP_X1=0
  CROP_Y1=0
  CROP_X2=4096
  CROP_Y2=2160

  IMG_DIR=${SOURCE_FOLDER}/${var_video_name}"/img"
  OUTPUT_DIR=${SOURCE_FOLDER}/${var_video_name}"/output"

  DET_DIR=${OUTPUT_DIR}"/det/csv"

  MODE_VEHICLES="vehicles"
  DYNAMIC_MODEL_VEHICLES="BM2"
  LABEL_REPLACE_VEHICLES="car"
  OUTPUT_VEHICLES_DIR=${OUTPUT_DIR}/${MODE_VEHICLES}
  DET_ASSO_VEHICLES_DIR=${OUTPUT_VEHICLES_DIR}"/det_association/csv"
  TRAJ_VEHICLES_DIR=${OUTPUT_VEHICLES_DIR}"/traj/csv"
  TRACK_MERGE_VEHICLES=${OUTPUT_VEHICLES_DIR}"/det_association/"${NAME}"_tracks_merge.csv"
  TRAJ_VEHICLES=${TRAJ_VEHICLES_DIR}/${NAME}"_traj.csv"
  TRAJ_INSPECT_VEHICLES_DIR=${OUTPUT_VEHICLES_DIR}"/traj_inspect/csv"
  TRAJ_INSPECT_VEHICLES=${TRAJ_INSPECT_VEHICLES_DIR}/${NAME}"_traj.csv"

  MODE_PEDESTRIANS="pedestrians"
  DYNAMIC_MODEL_PEDESTRIANS="CV"
  LABEL_REPLACE_PEDESTRIANS="person"
  OUTPUT_PEDESTRIANS_DIR=${OUTPUT_DIR}/${MODE_PEDESTRIANS}
  DET_ASSO_PEDESTRIANS_DIR=${OUTPUT_PEDESTRIANS_DIR}"/det_association/csv"
  TRAJ_PEDESTRIANS_DIR=${OUTPUT_PEDESTRIANS_DIR}"/traj/csv"
  TRACK_MERGE_PEDESTRIANS=${OUTPUT_PEDESTRIANS_DIR}"/det_association/"${NAME}"_tracks_merge.csv"
  TRAJ_PEDESTRIANS=${TRAJ_PEDESTRIANS_DIR}/${NAME}"_traj.csv"
  TRAJ_INSPECT_PEDESTRIANS_DIR=${OUTPUT_PEDESTRIANS_DIR}"/traj_inspect/csv"
  TRAJ_INSPECT_PEDESTRIANS=${TRAJ_INSPECT_PEDESTRIANS_DIR}/${NAME}"_traj.csv"

  # ========================================================================== #
  # 执行 Python 操作
  # ========================================================================== #

  ##################################################################
  # EXTRACTING FRAMES FROM VIDEO
  ##################################################################
  python traj_ext/object_det/run_saveimages.py ${VIDEO_NAME} -o ${SOURCE_FOLDER}/${var_video_name} --skip 3 --max_frame_num 60
  # python traj_ext/object_det/run_saveimages.py ${VIDEO_NAME} -o ${SOURCE_FOLDER}/${var_video_name} --skip 3 --max_frame_num 60000
  # python traj_ext/object_det/run_saveimages.py ${VIDEO_NAME} -o ${SOURCE_FOLDER}/${var_video_name} --skip 3 --frame_start 3500 --max_frame_num 4450
  # python traj_ext/object_det/run_saveimages.py ${VIDEO_NAME} -o ${SOURCE_FOLDER}/${var_video_name} --skip 3 --frame_start 5050 --max_frame_num 5450
  # python traj_ext/object_det/run_saveimages.py ${VIDEO_NAME} -o ${SOURCE_FOLDER}/${var_video_name} --skip 3 --frame_start 6125 --max_frame_num 6875


  ####################################################################
  # OBJECT DETECTION
  ####################################################################
  python traj_ext/object_det/mask_rcnn/run_detections_csv.py \
    -image_dir ${IMG_DIR} \
    -output_dir ${OUTPUT_DIR} \
    -crop_x1y1x2y2 ${CROP_X1} ${CROP_Y1} ${CROP_X2} ${CROP_Y2} \
    -no_save_images


  ####################################################################
  # VEHICLES
  ####################################################################

  # Det association
  python traj_ext/det_association/run_det_association.py \
    -image_dir ${IMG_DIR} \
    -output_dir ${OUTPUT_VEHICLES_DIR} \
    -det_dir ${DET_DIR} \
    -ignore_detection_area ${SOURCE_FOLDER}/${IGNORE_AREA_VEHICLES} \
    -det_zone_im ${SOURCE_FOLDER}/${DET_ZONE_IM_VEHICLES} \
    -mode ${MODE_VEHICLES} \
    -no_save_images


  # Process
  python traj_ext/postprocess_track/run_postprocess.py \
    -image_dir ${IMG_DIR} \
    -output_dir ${OUTPUT_VEHICLES_DIR} \
    -det_dir ${DET_DIR} \
    -det_asso_dir ${DET_ASSO_VEHICLES_DIR} \
    -track_merge ${TRACK_MERGE_VEHICLES} \
    -camera_street ${SOURCE_FOLDER}/${CAMERA_STREET} \
    -camera_sat  ${SOURCE_FOLDER}/${CAMERA_SAT} \
    -camera_sat_img ${SOURCE_FOLDER}/${CAMERA_SAT_IMG} \
    -det_zone_fned ${SOURCE_FOLDER}/${DET_ZONE_FNED_VEHICLES} \
    -delta_ms ${DELTA_MS} \
    -location_name ${LOCATION_NAME} \
    -dynamic_model ${DYNAMIC_MODEL_VEHICLES} \
    -date ${DATE} \
    -start_time ${START_TIME} \
    -no_save_images


  python traj_ext/visualization/run_inspect_traj.py \
    -traj ${TRAJ_VEHICLES} \
    -image_dir ${IMG_DIR} \
    -det_dir ${DET_DIR} \
    -det_asso_dir ${DET_ASSO_VEHICLES_DIR} \
    -track_merge ${TRACK_MERGE_VEHICLES} \
    -camera_street ${SOURCE_FOLDER}/${CAMERA_STREET} \
    -camera_sat  ${SOURCE_FOLDER}/${CAMERA_SAT} \
    -camera_sat_img ${SOURCE_FOLDER}/${CAMERA_SAT_IMG} \
    -det_zone_fned ${SOURCE_FOLDER}/${DET_ZONE_FNED_VEHICLES} \
    -label_replace ${LABEL_REPLACE_VEHICLES} \
    -output_dir ${OUTPUT_VEHICLES_DIR} \
    -hd_map ${SOURCE_FOLDER}/${HD_MAP} \
    -delta_ms ${DELTA_MS} \
    -location_name ${LOCATION_NAME} \
    -date ${DATE} \
    -start_time ${START_TIME} \
    -export

  ###################################################################
  # PEDESTRIAN
  ###################################################################

  # Det association
  python traj_ext/det_association/run_det_association.py \
    -image_dir ${IMG_DIR} \
    -output_dir ${OUTPUT_PEDESTRIANS_DIR} \
    -det_dir ${DET_DIR} \
    -ignore_detection_area ${SOURCE_FOLDER}/${IGNORE_AREA_PEDESTRIANS} \
    -det_zone_im ${SOURCE_FOLDER}/${DET_ZONE_IM_PEDESTRIANS} \
    -mode ${MODE_PEDESTRIANS} \
    -no_save_images

  # Process
  python traj_ext/postprocess_track/run_postprocess.py \
    -image_dir ${IMG_DIR} \
    -output_dir ${OUTPUT_PEDESTRIANS_DIR} \
    -det_dir ${DET_DIR} \
    -det_asso_dir ${DET_ASSO_PEDESTRIANS_DIR} \
    -track_merge ${TRACK_MERGE_PEDESTRIANS} \
    -camera_street ${SOURCE_FOLDER}/${CAMERA_STREET} \
    -camera_sat  ${SOURCE_FOLDER}/${CAMERA_SAT} \
    -camera_sat_img ${SOURCE_FOLDER}/${CAMERA_SAT_IMG} \
    -det_zone_fned ${SOURCE_FOLDER}/${DET_ZONE_FNED_PEDESTRIANS} \
    -delta_ms ${DELTA_MS} \
    -location_name ${LOCATION_NAME} \
    -dynamic_model ${DYNAMIC_MODEL_PEDESTRIANS} \
    -date ${DATE} \
    -start_time ${START_TIME} \
    -no_save_images


  python traj_ext/visualization/run_inspect_traj.py \
    -traj ${TRAJ_PEDESTRIANS} \
    -image_dir ${IMG_DIR} \
    -det_dir ${DET_DIR} \
    -det_asso_dir ${DET_ASSO_PEDESTRIANS_DIR} \
    -track_merge ${TRACK_MERGE_PEDESTRIANS} \
    -camera_street ${SOURCE_FOLDER}/${CAMERA_STREET} \
    -camera_sat  ${SOURCE_FOLDER}/${CAMERA_SAT} \
    -camera_sat_img ${SOURCE_FOLDER}/${CAMERA_SAT_IMG} \
    -det_zone_fned ${SOURCE_FOLDER}/${DET_ZONE_FNED_PEDESTRIANS} \
    -label_replace ${LABEL_REPLACE_PEDESTRIANS} \
    -output_dir ${OUTPUT_PEDESTRIANS_DIR} \
    -hd_map ${SOURCE_FOLDER}/${HD_MAP} \
    -delta_ms ${DELTA_MS} \
    -location_name ${LOCATION_NAME} \
    -date ${DATE} \
    -start_time ${START_TIME} \
    -export

  ###################################################################
  # VISUALIZATION
  ###################################################################

  python traj_ext/visualization/run_visualizer.py \
    -traj ${TRAJ_INSPECT_VEHICLES} \
    -traj_person ${TRAJ_INSPECT_PEDESTRIANS} \
    -image_dir ${IMG_DIR} \
    -camera_street ${SOURCE_FOLDER}/${CAMERA_STREET} \
    -camera_sat  ${SOURCE_FOLDER}/${CAMERA_SAT} \
    -camera_sat_img ${SOURCE_FOLDER}/${CAMERA_SAT_IMG} \
    -det_zone_fned ${SOURCE_FOLDER}/${DET_ZONE_FNED_VEHICLES} \
    -hd_map ${SOURCE_FOLDER}/${HD_MAP} \
    -output_dir ${OUTPUT_DIR} \
    -export 1


  ###################################################################
  # 结果保存为 gif
  ###################################################################
  python util_create_gif.py \
    --img_seq_dir ${OUTPUT_DIR}"/visualizer/img_concat" \
    --gif_name ${GIF_NAME}

  return
}

# ============================================================================ #
# 逐个处理视频
# ============================================================================ #
# 读取视频路径
file_video_dir="test_alaco/video_dir.txt"
while read line; do
  if [[ ${#line} -lt 1 ]]; then
    text_warn "skip empty line"
    continue
  fi
  if [[ ${line} =~ ^#.* ]]; then
    text_warn "ignore ${line}"
    continue
  fi
  VIDEOS_DIR=${line}
done < ${file_video_dir}

# 读取视频文件名
video_names_list="test_alaco/video_list.txt"
while read line; do
  # echo ${line}
  if [[ ${#line} -lt 1 ]]; then
    text_warn "skip empty line"
    continue
  fi

  if [[ ${line} =~ ^#.* ]]; then
    text_warn "ignore ${line}"
    continue
  fi

  echo "process ${line}"
  alaco_video_demo ${VIDEOS_DIR} ${line}

done < ${video_names_list}

# ============================================================================ #
# </batch run alaco videos >
# ============================================================================ #

time_sh_end=$(date +"%s.%N")
time_diff_sh=$(bc <<< "$time_sh_end - $time_sh_start")
text_warn "batch_run_alaco_videos.sh elapsed:  $time_diff_sh   seconds. ($time_sh_end - $time_sh_start)"
