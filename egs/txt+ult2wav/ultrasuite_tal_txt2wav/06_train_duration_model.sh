#!/bin/bash -e

if test "$#" -ne 2; then
    echo "################################"
    echo "Usage:"
    echo "./03_train_duration_model.sh <speaker> <path_to_duration_conf_file>"
    echo ""
    echo "Default path to duration conf file: conf/duration_${Voice}.conf"
    echo "################################"
    exit 1
fi

speaker=$1
duration_conf_file=$2

global_config_file=conf/global_settings_${speaker}.cfg
source $global_config_file

### Step 3: train duration model ###
echo "Step 3:"
echo "training duration model..."
./scripts/submit.sh ${MerlinDir}/src/run_merlin.py $duration_conf_file


