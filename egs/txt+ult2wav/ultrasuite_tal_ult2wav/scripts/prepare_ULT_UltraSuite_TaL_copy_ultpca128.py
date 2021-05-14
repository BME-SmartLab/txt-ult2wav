'''
## txt2ult

Written by Tamas Gabor Csapo <csapot@tmit.bme.hu>
First version March 1, 2021
'''

import sys
import os

if len(sys.argv) != 3:
    print('usage: python3 prepare_ULT_UltraSuite_TaL_copy_ultpca128.py <UltraSuite-TaL dir> <speaker>')
    print('Number of arguments:', len(sys.argv))
    print('Argument List:', str(sys.argv))
    dir_base = '~/UltraSuite-TaL/TaL80/core/'
    speaker = '01fi'
else:
    dir_base = sys.argv[1]
    speaker = sys.argv[2]
    if not os.path.isdir(dir_base + speaker):
        print(dir_base, speaker, 'directories not OK')
        raise

import numpy as np

n_pca = 128


# collect all possible ult files
ult_files_all = []
dir_data = dir_base + speaker + '/'
if os.path.isdir(dir_data):
    for file in sorted(os.listdir(dir_data)):
        # collect _aud and _xaud files
        if file.endswith('.ultpca128'):
            ult_files_all += [dir_data + file[:-10]]

for basefile in ult_files_all:
    print('cutting and copying', basefile)
    
    ult_as_pca = np.fromfile(basefile + '.ultpca128', dtype=np.float32).reshape(-1, n_pca)
    
    # cut ultrasound to length of speech
    
    # read lf0 file
    lf0 = np.fromfile(speaker + '_data/feats/lf0/' + os.path.basename(basefile) + '.lf0', dtype=np.float32)
    
    ult_as_pca = ult_as_pca[0:len(lf0)]
    
    if len(ult_as_pca) != len(lf0):
        print('lengths not equal, ', len(ult_as_pca), len(lf0))
        raise
    
    ult_as_pca.astype('float32').tofile(speaker + '_data/feats/ultpca128/' + os.path.basename(basefile) + '.ultpca128')
    
    # raise