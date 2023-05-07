@Echo off
Setlocal
if "%~1" EQU "" goto s_syntax

:: https://ss64.com/nt/syntax-tdiff.html

:: Convert start and end times to hundredths of a second
Call :s_calc_timecode %1
Set _start_timecode=%errorlevel%

Call :s_calc_timecode %2
Set _stop_timecode=%errorlevel%

:: Calculate the difference in hundredths
Set /a _diff_timecode=_stop_timecode - _start_timecode

:: Midnight rollover
if %_diff_timecode% LSS 0 set /a _diff_timecode+=(24 * 60 * 60 * 100)
Echo %_diff_timecode% hundredths of a second

:: Split out Hours, Mins etc and return the result
set /a hs=_diff_timecode %% 100
set /a _diff_timecode/=100
set /a ss=_diff_timecode %% 60
set /a _diff_timecode/=60
set /a mm=_diff_timecode %% 60
set /a _diff_timecode/=60
set /a hh=_diff_timecode

set hh=0%hh%
set mm=0%mm%
set ss=0%ss%
set hs=0%hs%

set _tdiff=%hh:~-2%:%mm:~-2%:%ss:~-2%.%hs:~-2%

Echo HH:MM:ss.hs
Echo %_tdiff%
endlocal & set _tdiff=%_tdiff%
goto :EOF


:s_calc_timecode
   :: Remove delimiters and convert to hundredths of a second.
  setlocal

  For /f "usebackq tokens=1,2,3,4 delims=:." %%a in ('%1') Do (
      set hh=00%%a
      set mm=00%%b
      set ss=00%%c
      set hs=00%%d
  )
   set hh=%hh:~-2%
   set mm=%mm:~-2%
   set ss=%ss:~-2%
   set hs=%hs:~-2%
   set /a hh=((%hh:~0,1% * 10) + %hh:~1,1%) * 60 * 60 * 100
   set /a mm=((%mm:~0,1% * 10) + %mm:~1,1%) * 60 * 100
   set /a ss=((%ss:~0,1% * 10) + %ss:~1,1%) * 100
   set /a hs=((%hs:~0,1% * 10) + %hs:~1,1%)
   
   set /a _timecode=hh + mm + ss + hs

Endlocal & Exit /b %_timecode%

:s_syntax
   Echo:
   Echo Syntax: tdiff.cmd StartTime StopTime
   Echo:
   Echo    The times can be given in the format:
   Echo    HH  or  HH:MM  or  HH:MM:ss  or  HH:MM:ss.hs
   Echo:
   Echo    so for example:  tdiff %%time%% 23
   Echo    will give the time difference between now and 23:00:00.00
   Echo:
   Echo The result is returned in variable %%_tdiff%%
Exit /b 1