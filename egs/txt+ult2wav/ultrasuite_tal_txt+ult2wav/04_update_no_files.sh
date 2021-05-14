#!/bin/bash -e

if test "$#" -ne 1; then
    echo "Usage: ./03b_update_no_files.sh <speaker>"
	speaker='01fi'
    # exit 1
	# ./03b_update_no_files.sh 02fe
else
	speaker=$1
fi

global_config_file=conf/global_settings_${speaker}.cfg

SED=sed
if [[ "$OSTYPE" == "darwin"* ]]; then
  which gsed > /dev/null
  if [[ "$?" != 0 ]]; then
    echo "You need to install GNU sed with 'brew install gnu-sed' on osX"
    exit 1
  fi
  SED=gsed
fi
no_lab_files=`ls ${speaker}_data/labels/label_state_align | wc -l`
no_lab_files_train=`echo "$no_lab_files" | awk '{print int(0.85 * $1)}'`
no_lab_files_valid=`echo "$no_lab_files" | awk '{print int(0.1 * $1)}'`
no_lab_files_test=`echo "$no_lab_files" "$no_lab_files_train" "$no_lab_files_valid" | awk '{print $1 - $2 - $3}'`
$SED -i s#'Train=.*'#'Train='${no_lab_files_train}# $global_config_file
$SED -i s#'Valid=.*'#'Valid='${no_lab_files_valid}# $global_config_file
$SED -i s#'Test=.*'#'Test='${no_lab_files_test}# $global_config_file

echo 'no. of train, valid, test files updated in ' $global_config_file $no_lab_files_train $no_lab_files_valid $no_lab_files_test
