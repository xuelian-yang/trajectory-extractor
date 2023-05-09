@echo off

Rem https://www.tutorialspoint.com/batch_script/batch_script_commands.htm
:: @echo on
:: echo echo turned on

echo.
call :text_debug "============================================================="

set message="run_calib @ windows"
call :header_warn %message%

:: 计时开始
:: call timer.cmd Start
set time_sh_start=%time%
:: =============================================================================
set alaco_temp_dir=E:/Github/trajectory-extractor/temp/calib_feature_parser
set alaco_input_dir=E:/Github/trajectory-extractor/test_alaco/hdmap_calib
set json_ext=.json
set png_ext=.png

set png_name_cam=10.10.145.232
set feat_name_cam=feature_points_%png_name_cam%
set png_name_hd=hdmap_0
set feat_name_hd=feature_points_%png_name_hd%

:: 生成标定输入
python traj_ext/camera_calib/calib_feature_parser.py ^
  --labelme_json %feat_name_cam%%json_ext%

python traj_ext/camera_calib/calib_feature_parser.py ^
  --labelme_json %feat_name_hd%%json_ext%

:: 标定
python traj_ext/camera_calib/run_calib_manual.py ^
  -calib_points %alaco_temp_dir%/%feat_name_cam%%json_ext%_camera_calib_manual_latlon.csv ^
  -image %alaco_input_dir%/%png_name_cam%%png_ext%

python traj_ext/camera_calib/run_calib_manual.py ^
  -calib_points %alaco_temp_dir%/%feat_name_hd%%json_ext%_camera_calib_manual_latlon.csv ^
  -image %alaco_input_dir%/%png_name_hd%%png_ext%

:: 手动选取检测区域
python traj_ext/camera_calib/run_detection_zone.py ^
  -camera_street %alaco_input_dir%/%png_name_cam%_cfg.yml ^
  -image_street %alaco_input_dir%/%png_name_cam%%png_ext% ^
  -camera_sat %alaco_input_dir%/%png_name_hd%_cfg.yml ^
  -image_sat %alaco_input_dir%/%png_name_hd%%png_ext%

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
