#!/bin/bash


if test "$#" -ne 4; then
    echo "################################"
    echo "Usage:"
    echo "./03_prepare_acoustic_features.sh <UltraSuite-TaL dir> <speaker> <path_to_wav_dir> <path_to_feat_dir>"
    echo ""
    echo "default path to wav dir(Input): database/wav"
    echo "default path to feat dir(Output): database/feats"
    echo "################################"
    exit 1
fi

ultrasuite_tal_dir=$1
speaker=$2
wav_dir=$3
feat_dir=$4

global_config_file=conf/global_settings_${speaker}.cfg
source $global_config_file


if [ ! "$(ls -A ${wav_dir})" ]; then
    echo "Please place your audio files in: ${wav_dir}"
    exit 1
fi

####################################
##### prepare vocoder features #####
####################################

prepare_feats=true
copy=true

# WORLD vocoder features
if [ "$prepare_feats" = true ]; then
    echo "Step 3:" 
    # echo "Prepare acoustic features using "${Vocoder}" vocoder..."
    python ${MerlinDir}/misc/scripts/vocoder/${Vocoder,,}/extract_features_for_merlin.py ${MerlinDir} ${wav_dir} ${feat_dir} $SamplingFreq 
fi

# ultrasound features - length should be the same as lf0!!!
echo "Prepare articulatory features ..."
mkdir -p ${feat_dir}/ultpca128
python3 scripts/prepare_ULT_UltraSuite_TaL_copy_ultpca128.py ${ultrasuite_tal_dir} ${speaker}

if [ "$copy" = true ]; then
    echo "Copying features to acoustic data directory..."
    acoustic_data_dir=experiments/${Voice}/acoustic_model/data
	mkdir -p $acoustic_data_dir
    cp -r ${feat_dir}/* $acoustic_data_dir
    echo "done...!"
fi
