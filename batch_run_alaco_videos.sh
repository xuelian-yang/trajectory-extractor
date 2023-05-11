#!/bin/bash

time_sh_start=$(date +"%s.%N")

# ============================================================================ #
# < batch run alaco videos >
# ============================================================================ #

video_names_list="test_alaco/video_list.txt"
while read line; do
  echo ${line}
done < ${video_names_list}

# ============================================================================ #
# </batch run alaco videos >
# ============================================================================ #

function text_warn() {
  echo -e "\e[33m# $1\e[39m"
}

time_sh_end=$(date +"%s.%N")
time_diff_sh=$(bc <<< "$time_sh_end - $time_sh_start")
text_warn "batch_run_alaco_videos.sh elapsed:  $time_diff_sh   seconds. ($time_sh_end - $time_sh_start)"
