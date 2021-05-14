#!/bin/bash

if test "$#" -ne 2; then
    echo "################################"
    echo "Usage: ./01_setup.sh <UltraSuite-TaL dir> <speaker>"
    echo "To run on sample data:"
    echo "./01_setup.sh ~/UltraSuite-TaL/TaL80/core/ 01fi"
    echo "################################"
    exit 1
fi

### Step 1: setup directories and the training data files ###
echo "Step 1:"

current_working_dir=$(pwd)
merlin_dir=$(dirname $(dirname $(dirname $current_working_dir)))
experiments_dir=${current_working_dir}/experiments

ultrasuite_tal_dir=$1
voice_name=$2
voice_dir=${experiments_dir}/${voice_name}

acoustic_dir=${voice_dir}/acoustic_model
duration_dir=${voice_dir}/duration_model
synthesis_dir=${voice_dir}/test_synthesis

mkdir -p ${experiments_dir}
mkdir -p ${voice_dir}
mkdir -p ${acoustic_dir}
mkdir -p ${duration_dir}


## copy file to directories from UltraSuite_TaL corpus
if [ -d "${ultrasuite_tal_dir}${voice_name}" ]
then
	data_dir=${voice_name}_data
else
    echo "The data for voice name ($voice_name) is not available...please use something from UltraSuite-TaL !!"
	echo "downloading UltraSuite-TaL data for speaker $voice_name"
	cd ${ultrasuite_tal_dir}
	rsync -av ultrasuite-rsync.inf.ed.ac.uk::tal-corpus/TaL80/core/${voice_name} .
	chmod 755 ${voice_name}
	cd ${current_working_dir}
	data_dir=${voice_name}_data
    # exit 1
fi

echo "deleting old files......"
# rm -fr ${data_dir}
rm -fr ${duration_dir}/data
rm -fr ${acoustic_dir}/data

# copying files here
mkdir -p ${data_dir}
mkdir -p ${data_dir}/txt
mkdir -p ${data_dir}/wav
mkdir -p ${data_dir}/lab

# preparing ultrasound data (e.g. cut wav files, create txt files)
python3 scripts/prepare_ULT_UltraSuite_TaL.py ${ultrasuite_tal_dir} ${voice_name}

echo "copying new files......"

cp ${ultrasuite_tal_dir}${voice_name}/*aud_cut_48k.wav ${data_dir}/wav/
for f in ${ultrasuite_tal_dir}${voice_name}/*aud.txt
do
	txt_file=`basename "$f"`
	txt_without_ext="${txt_file%%.*}"
	
	head -n 1 $f > ${data_dir}/txt/${txt_without_ext}_cut_48k.txt
done


echo "wav and txt are ready!"

global_config_file=conf/global_settings_${voice_name}.cfg

### default settings ###
echo "MerlinDir=${merlin_dir}" >  $global_config_file
echo "WorkDir=${current_working_dir}" >>  $global_config_file
echo "Voice=${voice_name}" >> $global_config_file
echo "Labels=state_align" >> $global_config_file
# echo "QuestionFile=questions-radio_dnn_416.hed" >> $global_config_file
echo "QuestionFile=questions-radio_dnn_1.hed" >> $global_config_file
echo "Vocoder=WORLD" >> $global_config_file
echo "SamplingFreq=48000" >> $global_config_file
echo "SilencePhone='sil'" >> $global_config_file

# TODO: update train-valid-test after labels are created
echo "FileIDList=file_id_list_full.scp" >> $global_config_file
echo "Train=180" >> $global_config_file 
echo "Valid=10" >> $global_config_file 
echo "Test=10" >> $global_config_file 


echo "######################################" >> $global_config_file
echo "############# TOOLS ##################" >> $global_config_file
echo "######################################" >> $global_config_file
echo "" >> $global_config_file

echo "ESTDIR=${merlin_dir}/tools/speech_tools" >> $global_config_file
echo "FESTDIR=${merlin_dir}/tools/festival" >> $global_config_file
echo "FESTVOXDIR=${merlin_dir}/tools/festvox" >> $global_config_file
echo "" >> $global_config_file
echo "HTKDIR=${merlin_dir}/tools/bin/htk" >> $global_config_file
echo "" >> $global_config_file
echo "tools done"

echo "Merlin default voice settings configured in $global_config_file"
echo "setup done...!"

