@echo off

:: 参考 run_trajectory_extraction.bat

Rem https://www.tutorialspoint.com/batch_script/batch_script_commands.htm
:: @echo on
:: echo echo turned on

echo.
call :text_debug "============================================================="

set message="batch_run_alaco_videos.bat @ windows"
call :header_warn %message%

:: 计时开始
:: call timer.cmd Start
set time_sh_start=%time%

:: =============================================================================
set VIDEOS_DIR=E:/Github/trajectory-extractor/test_alaco/temp_video/multi-stream-reocrds/2023-05-09_14_18_54

:: set camera_name=""
:: 注意: for 命令括号内不可有 :: 注释，但可用 REM
for /f "delims=" %%x in (test_alaco/video_list.txt) do (
    REM call :text_info "process %%x"
    call :process_alaco_video %%x
)

goto :end_of_commands


:: ALACO Demo 参数
:: 数据路径
set CASE_NAME=alaco_W92_2023-05-09_14_18_54
:: set SOURCE_FOLDER=test_alaco/alaco_W92_2023-05-09_14_18_54
set SOURCE_FOLDER=test_alaco/%CASE_NAME%
set VIDEO_NAME=W92_2023-05-09_14_18_54.mp4
set NAME=W92_2023-05-09_14_18_54
set GIF_NAME=alaco_traj_demo_%CASE_NAME%.gif
set DELTA_MS=100
set LOCATION_NAME=alaco_W92
set DATE="20230509"
set START_TIME="1418"

:: 标定文件
set CAMERA_STREET=10.10.145.232_cfg.yml
set CAMERA_SAT=hdmap_0_cfg.yml
set CAMERA_SAT_IMG=hdmap_0.png
:: TODO: 需要生成高精地图
:: set HD_MAP=brest_area1_street_hd_map.csv
set HD_MAP=""

:: SET DETECTION AD IGNORE ZONES
set DET_ZONE_IM_VEHICLES=10.10.145.232_detection_zone_im.yml
set DET_ZONE_FNED_VEHICLES=10.10.145.232_detection_zone.yml
set IGNORE_AREA_VEHICLES=""

set DET_ZONE_IM_PEDESTRIANS=10.10.145.232_detection_zone_im.yml
set DET_ZONE_FNED_PEDESTRIANS=10.10.145.232_detection_zone.yml
:: TODO: 生成行人忽略区域
set IGNORE_AREA_PEDESTRIANS=""

:: SET CROP VALUES FOR DETECTION HERE IF NEEDED
:: TODO: 设置裁剪区域
set CROP_X1=0
set CROP_Y1=0
set CROP_X2=4096
set CROP_Y2=2160

set IMG_DIR=%SOURCE_FOLDER%/img
set OUTPUT_DIR=%SOURCE_FOLDER%/output

call :text_warn %OUTPUT_DIR%

set DET_DIR=%OUTPUT_DIR%/det/csv

set MODE_VEHICLES=vehicles
set DYNAMIC_MODEL_VEHICLES=BM2
set LABEL_REPLACE_VEHICLES=car
set OUTPUT_VEHICLES_DIR=%OUTPUT_DIR%/%MODE_VEHICLES%
set DET_ASSO_VEHICLES_DIR=%OUTPUT_VEHICLES_DIR%/det_association/csv
set TRAJ_VEHICLES_DIR=%OUTPUT_VEHICLES_DIR%/traj/csv
set TRACK_MERGE_VEHICLES=%OUTPUT_VEHICLES_DIR%/det_association/%NAME%_tracks_merge.csv
set TRAJ_VEHICLES=%TRAJ_VEHICLES_DIR%/%NAME%_traj.csv
set TRAJ_INSPECT_VEHICLES_DIR=%OUTPUT_VEHICLES_DIR%/traj_inspect/csv
set TRAJ_INSPECT_VEHICLES=%TRAJ_INSPECT_VEHICLES_DIR%/%NAME%_traj.csv

set MODE_PEDESTRIANS=pedestrians
set DYNAMIC_MODEL_PEDESTRIANS=CV
set LABEL_REPLACE_PEDESTRIANS=person
set OUTPUT_PEDESTRIANS_DIR=%OUTPUT_DIR%/%MODE_PEDESTRIANS%
set DET_ASSO_PEDESTRIANS_DIR=%OUTPUT_PEDESTRIANS_DIR%/det_association/csv
set TRAJ_PEDESTRIANS_DIR=%OUTPUT_PEDESTRIANS_DIR%/traj/csv
set TRACK_MERGE_PEDESTRIANS=%OUTPUT_PEDESTRIANS_DIR%/det_association/%NAME%_tracks_merge.csv
set TRAJ_PEDESTRIANS=%TRAJ_PEDESTRIANS_DIR%/%NAME%_traj.csv
set TRAJ_INSPECT_PEDESTRIANS_DIR=%OUTPUT_PEDESTRIANS_DIR%/traj_inspect/csv
set TRAJ_INSPECT_PEDESTRIANS=%TRAJ_INSPECT_PEDESTRIANS_DIR%/%NAME%_traj.csv

:: ##################################################################
:: # EXTRACTING FRAMES FROM VIDEO
:: ##################################################################
set VIDEO_PATH=%SOURCE_FOLDER%/%VIDEO_NAME%

goto :skip_for_debug

python traj_ext/object_det/run_saveimages.py %VIDEO_PATH% --skip 3

:: ####################################################################
:: # OBJECT DETECTION
:: ####################################################################
python traj_ext/object_det/mask_rcnn/run_detections_csv.py ^
        -image_dir %IMG_DIR% ^
        -output_dir %OUTPUT_DIR% ^
        -crop_x1y1x2y2 %CROP_X1% %CROP_Y1% %CROP_X2% %CROP_Y2% ^
        -no_save_images


:: ####################################################################
:: # VEHICLES
:: ####################################################################
:: # Det association
python traj_ext/det_association/run_det_association.py ^
            -image_dir %IMG_DIR% ^
            -output_dir %OUTPUT_VEHICLES_DIR% ^
            -det_dir %DET_DIR% ^
            -ignore_detection_area %SOURCE_FOLDER%/%IGNORE_AREA_VEHICLES% ^
            -det_zone_im %SOURCE_FOLDER%/%DET_ZONE_IM_VEHICLES% ^
            -mode %MODE_VEHICLES% ^
            -no_save_images

:: # Process
python traj_ext/postprocess_track/run_postprocess.py ^
            -image_dir %IMG_DIR% ^
            -output_dir %OUTPUT_VEHICLES_DIR% ^
            -det_dir %DET_DIR% ^
            -det_asso_dir %DET_ASSO_VEHICLES_DIR% ^
            -track_merge %TRACK_MERGE_VEHICLES% ^
            -camera_street %SOURCE_FOLDER%/%CAMERA_STREET% ^
            -camera_sat  %SOURCE_FOLDER%/%CAMERA_SAT% ^
            -camera_sat_img %SOURCE_FOLDER%/%CAMERA_SAT_IMG% ^
            -det_zone_fned %SOURCE_FOLDER%/%DET_ZONE_FNED_VEHICLES% ^
            -delta_ms %DELTA_MS% ^
            -location_name %LOCATION_NAME% ^
            -dynamic_model %DYNAMIC_MODEL_VEHICLES% ^
            -date %DATE% ^
            -start_time %START_TIME% ^
            -no_save_images

python traj_ext/visualization/run_inspect_traj.py ^
            -traj %TRAJ_VEHICLES% ^
            -image_dir %IMG_DIR% ^
            -det_dir %DET_DIR% ^
            -det_asso_dir %DET_ASSO_VEHICLES_DIR% ^
            -track_merge %TRACK_MERGE_VEHICLES% ^
            -camera_street %SOURCE_FOLDER%/%CAMERA_STREET% ^
            -camera_sat  %SOURCE_FOLDER%/%CAMERA_SAT% ^
            -camera_sat_img %SOURCE_FOLDER%/%CAMERA_SAT_IMG% ^
            -det_zone_fned %SOURCE_FOLDER%/%DET_ZONE_FNED_VEHICLES% ^
            -label_replace %LABEL_REPLACE_VEHICLES% ^
            -output_dir %OUTPUT_VEHICLES_DIR% ^
            -hd_map %SOURCE_FOLDER%/%HD_MAP% ^
            -delta_ms %DELTA_MS% ^
            -location_name %LOCATION_NAME% ^
            -date %DATE% ^
            -start_time %START_TIME% ^
            -export

:: ###################################################################
:: # PEDESTRIAN
:: ###################################################################
:: # Det association
python traj_ext/det_association/run_det_association.py ^
            -image_dir %IMG_DIR% ^
            -output_dir %OUTPUT_PEDESTRIANS_DIR% ^
            -det_dir %DET_DIR% ^
            -ignore_detection_area %SOURCE_FOLDER%/%IGNORE_AREA_PEDESTRIANS% ^
            -det_zone_im %SOURCE_FOLDER%/%DET_ZONE_IM_PEDESTRIANS% ^
            -mode %MODE_PEDESTRIANS% ^
            -no_save_images

:: # Process
python traj_ext/postprocess_track/run_postprocess.py ^
            -image_dir %IMG_DIR% ^
            -output_dir %OUTPUT_PEDESTRIANS_DIR% ^
            -det_dir %DET_DIR% ^
            -det_asso_dir %DET_ASSO_PEDESTRIANS_DIR% ^
            -track_merge %TRACK_MERGE_PEDESTRIANS% ^
            -camera_street %SOURCE_FOLDER%/%CAMERA_STREET% ^
            -camera_sat  %SOURCE_FOLDER%/%CAMERA_SAT% ^
            -camera_sat_img %SOURCE_FOLDER%/%CAMERA_SAT_IMG% ^
            -det_zone_fned %SOURCE_FOLDER%/%DET_ZONE_FNED_PEDESTRIANS% ^
            -delta_ms %DELTA_MS% ^
            -location_name %LOCATION_NAME% ^
            -dynamic_model %DYNAMIC_MODEL_PEDESTRIANS% ^
            -date %DATE% ^
            -start_time %START_TIME% ^
            -no_save_images


python traj_ext/visualization/run_inspect_traj.py ^
            -traj %TRAJ_PEDESTRIANS% ^
            -image_dir %IMG_DIR% ^
            -det_dir %DET_DIR% ^
            -det_asso_dir %DET_ASSO_PEDESTRIANS_DIR% ^
            -track_merge %TRACK_MERGE_PEDESTRIANS% ^
            -camera_street %SOURCE_FOLDER%/%CAMERA_STREET% ^
            -camera_sat  %SOURCE_FOLDER%/%CAMERA_SAT% ^
            -camera_sat_img %SOURCE_FOLDER%/%CAMERA_SAT_IMG% ^
            -det_zone_fned %SOURCE_FOLDER%/%DET_ZONE_FNED_PEDESTRIANS% ^
            -label_replace %LABEL_REPLACE_PEDESTRIANS% ^
            -output_dir %OUTPUT_PEDESTRIANS_DIR% ^
            -hd_map %SOURCE_FOLDER%/%HD_MAP% ^
            -delta_ms %DELTA_MS% ^
            -location_name %LOCATION_NAME% ^
            -date %DATE% ^
            -start_time %START_TIME% ^
            -export

:skip_for_debug
:: ###################################################################
:: # VISUALIZATION
:: ###################################################################
python traj_ext/visualization/run_visualizer.py ^
            -traj %TRAJ_INSPECT_VEHICLES% ^
            -traj_person %TRAJ_INSPECT_PEDESTRIANS% ^
            -image_dir %IMG_DIR% ^
            -camera_street %SOURCE_FOLDER%/%CAMERA_STREET% ^
            -camera_sat  %SOURCE_FOLDER%/%CAMERA_SAT% ^
            -camera_sat_img %SOURCE_FOLDER%/%CAMERA_SAT_IMG% ^
            -det_zone_fned %SOURCE_FOLDER%/%DET_ZONE_FNED_VEHICLES% ^
            -output_dir %OUTPUT_DIR% ^
            -export 1

goto :end_of_commands
:: ###################################################################
:: 结果保存为 gif
:: ###################################################################
python util_create_gif.py ^
  --case_name %CASE_NAME% ^
  --gif_name %GIF_NAME%

:end_of_commands
:: =============================================================================
:: 计时结束
:: call timer.cmd Stop
set time_sh_end=%time%

:: 计算耗时
call tdiff.cmd %time_sh_start% %time_sh_end%

goto :EOF

:: =============================================================================
:: reference:
::    https://stackoverflow.com/a/38617204
::    https://gist.githubusercontent.com/mlocati/fdabcaeb8071d5c75a2d51712db24011/raw/b710612d6320df7e146508094e84b92b34c77d48/win10colors.cmd

:header_error
:: 91m red
echo [91m##################################################[0m
echo [91m# %~1[0m
echo [91m##################################################[0m
echo.
exit /b 0

:header_warn
:: 93m yellow
echo [93m##################################################[0m
echo [93m# %~1[0m
echo [93m##################################################[0m
echo.
exit /b 0

:header_info
:: 92m green
echo [92m##################################################[0m
echo [92m# %~1[0m
echo [92m##################################################[0m
echo.
exit /b 0

:header_debug
:: 94m blue
echo [94m##################################################[0m
echo [94m# %~1[0m
echo [94m##################################################[0m
echo.
exit /b 0

:text_error
:: 91m red
echo [91m# %~1[0m
exit /b 0

:text_warn
:: 93m yellow
echo [93m# %~1[0m
exit /b 0

:text_info
:: 92m green
echo [92m# %~1[0m
exit /b 0

:text_debug
:: 94m blue
echo [94m# %~1[0m
exit /b 0

:: =============================================================================
:: < 批量处理视频文件 >
:: =============================================================================
:process_alaco_video
set var_video_name=%~1
REM call :text_info %var_video_name%
if %var_video_name:~0,1%==# (
  call :text_warn "ignore %~1"
  exit /b 0
)

set var_camera_name=%var_video_name:~0,3%

:: 获取相机编码对应的 IP
REM call :text_info %var_camera_name%

if "%var_camera_name%"=="W91" (
  set var_camera_ip="10.10.145.231"
) else if "%var_camera_name%"=="W92" (
  set var_camera_ip="10.10.145.232"
) else if "%var_camera_name%"=="W93" (
  set var_camera_ip="10.10.145.233"
) else if "%var_camera_name%"=="W94" (
  set var_camera_ip="10.10.145.234"
) else (
  call :text_warn "unknown camera name %var_camera_name%"
  exit /b 0
)

call :text_info "IP of %var_camera_name% is %var_camera_ip%"
:: call :text_debug ">> %VIDEOS_DIR%/%var_video_name%"
REM echo %VIDEOS_DIR%/%var_video_name%

:: ALACO Demo 参数
:: 数据路径
set CASE_NAME=alaco_cameras
set SOURCE_FOLDER=test_alaco/%CASE_NAME%
set VIDEO_NAME=%VIDEOS_DIR%/%var_video_name%.mp4
set NAME=%var_video_name%

REM 调试打印
REM echo %CASE_NAME%
REM echo %SOURCE_FOLDER%
echo %VIDEO_NAME%
REM echo %NAME%

set GIF_NAME=alaco_traj_demo_%var_camera_ip%_%CASE_NAME%.gif
set DELTA_MS=100
set LOCATION_NAME=alaco_%var_camera_name%
set DATE="20230509"
set START_TIME="1418"

:: 标定文件
set CAMERA_STREET=%var_camera_ip%_cfg.yml
set CAMERA_SAT=hdmap_0_cfg.yml
set CAMERA_SAT_IMG=hdmap_0.png
set HD_MAP=""

:: SET DETECTION AD IGNORE ZONES
set DET_ZONE_IM_VEHICLES=%var_camera_ip%_detection_zone_im.yml
set DET_ZONE_FNED_VEHICLES=%var_camera_ip%_detection_zone.yml
set IGNORE_AREA_VEHICLES=""

set DET_ZONE_IM_PEDESTRIANS=%var_camera_ip%_detection_zone_im.yml
set DET_ZONE_FNED_PEDESTRIANS=%var_camera_ip%_detection_zone.yml
:: TODO: 生成行人忽略区域
set IGNORE_AREA_PEDESTRIANS=""

:: SET CROP VALUES FOR DETECTION HERE IF NEEDED
:: TODO: 设置裁剪区域
set CROP_X1=0
set CROP_Y1=0
set CROP_X2=4096
set CROP_Y2=2160

set IMG_DIR=%SOURCE_FOLDER%/%var_video_name%/img
set OUTPUT_DIR=%SOURCE_FOLDER%/%var_video_name%/output

set DET_DIR=%OUTPUT_DIR%/det/csv

set MODE_VEHICLES=vehicles
set DYNAMIC_MODEL_VEHICLES=BM2
set LABEL_REPLACE_VEHICLES=car
set OUTPUT_VEHICLES_DIR=%OUTPUT_DIR%/%MODE_VEHICLES%
set DET_ASSO_VEHICLES_DIR=%OUTPUT_VEHICLES_DIR%/det_association/csv
set TRAJ_VEHICLES_DIR=%OUTPUT_VEHICLES_DIR%/traj/csv
set TRACK_MERGE_VEHICLES=%OUTPUT_VEHICLES_DIR%/det_association/%NAME%_tracks_merge.csv
set TRAJ_VEHICLES=%TRAJ_VEHICLES_DIR%/%NAME%_traj.csv
set TRAJ_INSPECT_VEHICLES_DIR=%OUTPUT_VEHICLES_DIR%/traj_inspect/csv
set TRAJ_INSPECT_VEHICLES=%TRAJ_INSPECT_VEHICLES_DIR%/%NAME%_traj.csv

set MODE_PEDESTRIANS=pedestrians
set DYNAMIC_MODEL_PEDESTRIANS=CV
set LABEL_REPLACE_PEDESTRIANS=person
set OUTPUT_PEDESTRIANS_DIR=%OUTPUT_DIR%/%MODE_PEDESTRIANS%
set DET_ASSO_PEDESTRIANS_DIR=%OUTPUT_PEDESTRIANS_DIR%/det_association/csv
set TRAJ_PEDESTRIANS_DIR=%OUTPUT_PEDESTRIANS_DIR%/traj/csv
set TRACK_MERGE_PEDESTRIANS=%OUTPUT_PEDESTRIANS_DIR%/det_association/%NAME%_tracks_merge.csv
set TRAJ_PEDESTRIANS=%TRAJ_PEDESTRIANS_DIR%/%NAME%_traj.csv
set TRAJ_INSPECT_PEDESTRIANS_DIR=%OUTPUT_PEDESTRIANS_DIR%/traj_inspect/csv
set TRAJ_INSPECT_PEDESTRIANS=%TRAJ_INSPECT_PEDESTRIANS_DIR%/%NAME%_traj.csv

:: ##################################################################
:: # EXTRACTING FRAMES FROM VIDEO
:: ##################################################################
python traj_ext/object_det/run_saveimages.py %VIDEO_NAME% -o %SOURCE_FOLDER%/%var_video_name% --skip 3


exit /b 0
:: =============================================================================
:: </批量处理视频文件 >
:: =============================================================================

:: End of File
