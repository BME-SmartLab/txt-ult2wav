#!/bin/bash


if test "$#" -ne 1; then
    echo "################################"
    echo "Usage: ./merlin_synthesis.sh  <speaker>"
    echo "################################"
    exit 1
fi

voice_name=$1

global_config_file=conf/global_settings_${voice_name}.cfg

if [ ! -f  $global_config_file ]; then
    echo "Please run steps from 1-5..."
    exit 1
else
    source $global_config_file
fi

### define few variables here
testDir=experiments/${voice_name}/test_synthesis

txt_dir=${testDir}/txt
txt_file=${testDir}/utts.data

mkdir -p $txt_dir
echo "I owe you a yoyo." > $txt_dir/sent1.txt
echo "aiaiaiai ai ai ai ai a i a i a i a i." > $txt_dir/sent2.txt
echo "eieieiei ei ei ei ei e i e i e i e i." > $txt_dir/sent3.txt
echo "This is the result of text-to-articulatory data prediction using ultrasound tongue imaging." > $txt_dir/sent4.txt


if [[ ! -d "${txt_dir}" ]] && [[ ! -f "${txt_file}" ]]; then
    echo "Please give text as input: either 1 or 2"
    echo "1. ${txt_dir}  -- a text directory containing text files"
    echo "2. ${txt_file} -- a single text file with each sentence in a new line in festival format"
    exit 1
fi


lab_dir=${testDir}

### Step 1: create label files from text ###
echo "Step 1: creating label files from text..."
# ./scripts/prepare_labels_from_txt.sh $global_config_file
./scripts/prepare_labels_from_txt.sh $txt_dir $lab_dir $global_config_file

status_step1=$?
if [ $status_step1 -eq 1 ]; then
    echo "Step 1 not successful !!"
    exit 1
fi

# copy lab files
cp $lab_dir/prompt-lab/*.lab $testDir/gen-lab/

### Step 2: synthesize speech   ###
echo "Step 2: synthesizing speech..."
./scripts/submit.sh ${MerlinDir}/src/run_merlin.py conf/test_dur_synth_${voice_name}.conf
./scripts/submit.sh ${MerlinDir}/src/run_merlin.py conf/test_synth_${voice_name}.conf

echo "deleting intermediate synthesis files..."
./scripts/remove_intermediate_files.sh $global_config_file

# echo "txt2ult"
# python3 scripts/generate_ult_video_txt2ult.py ${voice_name}

echo "synthesized audio and video files are in: experiments/${voice_name}/test_synthesis/wav"



