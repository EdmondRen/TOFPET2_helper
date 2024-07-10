#!/bin/bash



# Arg[1]: file to process
if [ $# -ge 1 ]; then
    base_filename=$(basename "$1" .root)
fi

# Arg[2]: output path.
# If not given, will save in the same folder as the data file.
if [ $# -ge 2 ]; then
    output_dir=$2
    echo "Output saved at ${output_dir}"
else
    output_dir=$(dirname "$1")
    echo "Output path not provided, save to the same folder of the raw file"
fi

timewindow=50

mapped_filename="${output_dir}/${base_filename}_hit.root"
triggered_filename="${output_dir}/${base_filename}_triggered.root"

# Convert raw hit to coordinates
echo
python script_mapping.py $1 ${mapped_filename}


# Group hits into events
echo 
python script_trigger.py ${mapped_filename} ${triggered_filename} ${timewindow}

# Track and vertex reconstruction
echo
echo "Finding tracks and vertices"
pytracker ${triggered_filename} ${output_dir}  --config=../configurations/pytracker_config.py --overwrite