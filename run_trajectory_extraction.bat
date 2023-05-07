@echo off

Rem https://www.tutorialspoint.com/batch_script/batch_script_commands.htm
:: @echo on
:: echo echo turned on

echo.
call :text_debug "============================================================="

set message="run_trajectory_extraction @ windows"
call :header_warn %message%

:: 计时开始
:: call timer.cmd Start
set time_sh_start=%time%

:: 延迟
:: timeout /T 3 /NOBREAK
:: ping -n 2 127.0.0.1>nul

:: =============================================================================
:: call :text_warn "%time%"
:: goto :EOF

:: # SET THE PATH AND CONFIG
set SOURCE_FOLDER="test_dataset/brest_20190609_130424_327_334"
set VIDEO_NAME="brest_20190609_130424_327_334.mp4"
set NAME="brest_20190609_130424_327_334"
set DELTA_MS=100
set LOCATION_NAME="brest"
set DATE="20190609"
set START_TIME="1310"

set CAMERA_STREET="brest_area1_street_cfg.yml"
set CAMERA_SAT="brest_area1_sat_cfg.yml"
set CAMERA_SAT_IMG="brest_area1_sat.png"
set HD_MAP="brest_area1_street_hd_map.csv"

:: # SET DETECTION AD IGNORE ZONES
set DET_ZONE_IM_VEHICLES="brest_area1_detection_zone_im.yml"
set DET_ZONE_FNED_VEHICLES="brest_area1_detection_zone.yml"
set IGNORE_AREA_VEHICLES=""

set DET_ZONE_IM_PEDESTRIANS="brest_area1_detection_zone_im.yml"
set DET_ZONE_FNED_PEDESTRIANS="brest_area1_detection_zone.yml"
set IGNORE_AREA_PEDESTRIANS="brest_area1_ignoreareas.csv"

:: # SET CROP VALUES FOR DETECTION HERE IF NEEDED
set CROP_X1=180
set CROP_Y1=120
set CROP_X2=1250
set CROP_Y2=720

set IMG_DIR="%SOURCE_FOLDER%/img"
set OUTPUT_DIR="%SOURCE_FOLDER%/output"

set DET_DIR="%OUTPUT_DIR%/det/csv"

set MODE_VEHICLES="vehicles"
set DYNAMIC_MODEL_VEHICLES="BM2"
set LABEL_REPLACE_VEHICLES="car"
set OUTPUT_VEHICLES_DIR="%OUTPUT_DIR%/%MODE_VEHICLES%"
set DET_ASSO_VEHICLES_DIR="%OUTPUT_VEHICLES_DIR%/det_association/csv"
set TRAJ_VEHICLES_DIR="%OUTPUT_VEHICLES_DIR%/traj/csv"
set TRACK_MERGE_VEHICLES="%OUTPUT_VEHICLES_DIR%/det_association/%NAME%_tracks_merge.csv"
set TRAJ_VEHICLES="%TRAJ_VEHICLES_DIR%/%NAME%_traj.csv"
set TRAJ_INSPECT_VEHICLES_DIR="%OUTPUT_VEHICLES_DIR%/traj_inspect/csv"
set TRAJ_INSPECT_VEHICLES="%TRAJ_INSPECT_VEHICLES_DIR%/%NAME%_traj.csv"

set MODE_PEDESTRIANS="pedestrians"
set DYNAMIC_MODEL_PEDESTRIANS="CV"
set LABEL_REPLACE_PEDESTRIANS="person"
set OUTPUT_PEDESTRIANS_DIR="%OUTPUT_DIR%}/%MODE_PEDESTRIANS%"
set DET_ASSO_PEDESTRIANS_DIR="%OUTPUT_PEDESTRIANS_DIR%/det_association/csv"
set TRAJ_PEDESTRIANS_DIR="%OUTPUT_PEDESTRIANS_DIR%/traj/csv"
set TRACK_MERGE_PEDESTRIANS="%OUTPUT_PEDESTRIANS_DIR%/det_association/%NAME%_tracks_merge.csv"
set TRAJ_PEDESTRIANS="%TRAJ_PEDESTRIANS_DIR%/%NAME%_traj.csv"
set TRAJ_INSPECT_PEDESTRIANS_DIR="%OUTPUT_PEDESTRIANS_DIR%/traj_inspect/csv"
set TRAJ_INSPECT_PEDESTRIANS="%TRAJ_INSPECT_PEDESTRIANS_DIR%/%NAME%_traj.csv"

:: ##################################################################
:: # EXTRACTING FRAMES FROM VIDEO
:: ##################################################################

set VIDEO_PATH="%SOURCE_FOLDER%/%VIDEO_NAME%"
python traj_ext/object_det/run_saveimages.py %VIDEO_PATH% --skip 3

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

:: End of File
