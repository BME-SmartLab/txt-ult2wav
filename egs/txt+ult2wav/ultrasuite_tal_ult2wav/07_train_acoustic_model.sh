#!/bin/bash -e


if test "$#" -ne 2; then
    echo "################################"
    echo "Usage:"
    echo "./04_train_acoustic_model.sh <path_to_acoustic_conf_file>"
    echo ""
    echo "Default path to acoustic conf file: conf/acoustic_${Voice}.conf"
    echo "################################"
    exit 1
fi

speaker=$1
acoustic_conf_file=$2

global_config_file=conf/global_settings_${speaker}.cfg
source $global_config_file


### Step 4: train acoustic model ###
echo "Step 4:"
echo "training acoustic model..."
./scripts/submit.sh ${MerlinDir}/src/run_merlin.py $acoustic_conf_file


