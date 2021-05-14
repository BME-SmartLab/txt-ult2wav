#!/bin/bash -e

if test "$#" -ne 2; then
    echo "Usage: ./run_full_voice.sh <UltraSuite-TaL dir> <speaker>"
	speaker='01fi'
	ultrasuite_tal_dir='~/UltraSuite-TaL/TaL80/core/'
    # exit 1
	# ./run_full_voice.sh ~/UltraSuite-TaL/TaL80/core/ 02fe
else
	ultrasuite_tal_dir=$1
	speaker=$2
fi


### setup directories and the training data files ###
./01_setup.sh ${ultrasuite_tal_dir} ${speaker}

### prepare labels
./02_prepare_labels.sh ${speaker} ${speaker}_data/wav ${speaker}_data/txt ${speaker}_data/labels

### extract acoustic features
./03_prepare_acoustic_features.sh ${ultrasuite_tal_dir} ${speaker} ${speaker}_data/wav ${speaker}_data/feats

### update number of train, valid, test files for global config
./04_update_no_files.sh ${speaker}

### prepare config files for training and testing
./05_prepare_conf_files.sh conf/global_settings_${speaker}.cfg

### train duration model
./06_train_duration_model.sh ${speaker} conf/duration_${speaker}.conf

### train acoustic model
./07_train_acoustic_model.sh ${speaker} conf/acoustic_${speaker}.conf

### synthesize speech ###
# ./08_merlin_synthesis.sh ${speaker}




