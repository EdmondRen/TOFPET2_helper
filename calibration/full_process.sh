#!/bin/bash

timewindow=50
base_filename=$(basename "$1" .root)
mapped_filename="$2"
mapped_filename="${mapped_filename}${base_filename}_hit.root"

python mapping_script.py $1 $2

python trigger_script.py ${mapped_filename} $2 ${timewindow}