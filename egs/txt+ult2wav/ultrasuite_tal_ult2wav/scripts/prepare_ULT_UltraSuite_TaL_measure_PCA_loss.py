'''
## txt2ult

Written by Tamas Gabor Csapo <csapot@tmit.bme.hu>
First version March 1, 2021
'''

import sys
import os

if len(sys.argv) != 3:
    print('usage: python3 prepare_ULT_UltraSuite_TaL.py <UltraSuite-TaL dir> <speaker>')
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
import matplotlib.pyplot as plt
import scipy.io.wavfile as io_wav
import pickle
from subprocess import call, check_output, run
import skimage


from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA


# read_ult reads in *.ult file from AAA
def read_ult(filename, NumVectors, PixPerVector):
    # read binary file
    ult_data = np.fromfile(filename, dtype='uint8')
    ult_data = np.reshape(ult_data, (-1, NumVectors, PixPerVector))
    return ult_data


def read_wav(filename):
    (Fs, x) = io_wav.read(filename)
    return (x, Fs)

def write_wav(x, Fs, filename):
    # scaled = np.int16(x / np.max(np.abs(x)) * 32767)
    io_wav.write(filename, Fs, np.int16(x))

# read_meta reads in *.txt ult metadata file from AAA
def read_param(filename):    
    NumVectors = 0
    PixPerVector = 0
    # read metadata from txt
    for line in open(filename):
        # 1st line: NumVectors=64
        if "NumVectors" in line:
            NumVectors = int(line[11:])
        # 2nd line: PixPerVector=842
        if "PixPerVector" in line:
            PixPerVector = int(line[13:])
        # 3rd line: ZeroOffset=210
        if "ZeroOffset" in line:
            ZeroOffset = int(line[11:])
        # 5th line: Angle=0,025
        if "Angle" in line:
            Angle = float(line[6:].replace(',', '.'))
        # 8th line: FramesPerSec=82,926
        # Warning: this FramesPerSec value is usually not real, use calculate_FramesPerSec function instead!
        if "FramesPerSec" in line:
            FramesPerSec = float(line[13:].replace(',', '.'))
        # 9th line: first frame
        # TimeInSecsOfFirstFrame=0.95846
        if "TimeInSecsOfFirstFrame" in line:
            TimeInSecsOfFirstFrame = float(line[23:].replace(',', '.'))
    
    return (NumVectors, PixPerVector, ZeroOffset, Angle, FramesPerSec, TimeInSecsOfFirstFrame)

def cut_and_resample_wav(filename_wav_in, Fs_target):
    filename_no_ext = filename_wav_in.replace('.wav', '')
    
    filename_param = filename_no_ext + '.param'
    filename_wav_out = filename_no_ext + '_cut_48k.wav'
    
    # resample speech using SoX
    command = 'sox ' + filename_wav_in + ' -r ' + str(Fs_target) + ' ' + \
              filename_no_ext + '_48k.wav'
    call(command, shell=True)
    
    # volume normalization using SoX
    command = 'sox --norm=-3 ' + filename_no_ext + '_48k.wav' + ' ' + \
              filename_no_ext + '_48k_volnorm.wav'
    call(command, shell=True)
    
    # cut from wav the signal the part where there are ultrasound frames
    (NumVectors, PixPerVector, ZeroOffset, Angle, FramesPerSec, TimeInSecsOfFirstFrame) = read_param(filename_param)
    (speech_wav_data, Fs_wav) = read_wav(filename_no_ext + '_48k_volnorm.wav')
    init_offset = int(TimeInSecsOfFirstFrame * Fs_wav) # initial offset in samples
    speech_wav_data = speech_wav_data[init_offset - hopLength : ]
    write_wav(speech_wav_data, Fs_wav, filename_wav_out)
    
    # remove temp files
    os.remove(filename_no_ext + '_48k.wav')
    os.remove(filename_no_ext + '_48k_volnorm.wav')
    
    print(filename_no_ext + ' - resampled, volume normalized, and cut to start with ultrasound')
    

# settings for UltraSuite-TaL
samplingFrequency = 48000
hopLength = 240 # 5 ms at 48 kHz
hopLength_UTI = 589 # 81.5 fps at 48 kHz

# parameters of ultrasound images, from .param file
n_lines = 64
n_pixels = 842
n_pixels_reduced = 128

# speakers = ['01fi', '02fe', '03mn', '04me', '05ms', '06fe', '07me', '08me', '09fe', '10me']

    
# collect all possible ult files
ult_files_all = []
dir_data = dir_base + speaker + '/'
if os.path.isdir(dir_data):
    for file in sorted(os.listdir(dir_data)):
        # collect _aud and _xaud files
        if file.endswith('aud.ult'):
            ult_files_all += [dir_data + file[:-4]]

# randomize the order of files
# random.shuffle(ult_files_all)

# temp: only first 10 sentence
# ult_files_all = ult_files_all[0:10]

ult_files = dict()
ult = dict()
ult_size = dict()

# train: first 85% of sentences
ult_files['train'] = ult_files_all[0:int(0.85*len(ult_files_all))]
# valid: next 10% of sentences
ult_files['valid'] = ult_files_all[int(0.85*len(ult_files_all)):int(0.95*len(ult_files_all))]
# test: last 5% of sentences
ult_files['test'] = ult_files_all[int(0.95*len(ult_files_all)):]

# only do the processing if the PCA file is not available
# if not os.path.isfile(speaker + '_data/UTI_to_PCA_' + speaker + '.sav'):
if True:
    for train_valid in ['train', 'valid', 'test']:
        n_max_ultrasound_frames = len(ult_files[train_valid]) * 1000
        ult[train_valid] = np.empty((n_max_ultrasound_frames, n_lines, n_pixels_reduced))
        ult_size[train_valid] = 0
        
        # load all training/validation data
        for basefile in ult_files[train_valid]:
            ult_data = read_ult(basefile + '.ult', n_lines, n_pixels)
            
            # resample / interpolate ult data to 5 ms frameshift
            
            # resample and cut if necessary
            if not os.path.isfile(basefile + '_cut_48k.wav'):
                cut_and_resample_wav(basefile + '.wav', samplingFrequency)
            
            print(basefile, ult_data.shape)
            
            if ult_size[train_valid] + len(ult_data) > n_max_ultrasound_frames:
                print('data too large', n_max_ultrasound_frames, ult_size[train_valid], len(ult_data))
                raise
            
            for i in range(len(ult_data)):
                ult[train_valid][ult_size[train_valid] + i] = skimage.transform.resize(ult_data[i], (n_lines, n_pixels_reduced), preserve_range=True) / 255
            
            
            ult_size[train_valid] += len(ult_data)
            
            print('n_frames_all: ', ult_size[train_valid])


        ult[train_valid] = ult[train_valid][0 : ult_size[train_valid]]
        ult[train_valid] = np.reshape(ult[train_valid], (-1, n_lines * n_pixels_reduced))
        
    ult_pca = dict()
    for n_pca in [2, 4, 8, 16, 32, 64, 128]: #, 256, 512]:
        print('calculating PCA with n', n_pca)
        ult_pca[n_pca] = PCA(n_components = n_pca)
        ult_pca[n_pca].fit(ult[train_valid])

        pickle.dump(ult_pca, open(speaker + '_data/UTI_to_PCA_' + speaker + '_' + str(n_pca) + '.sav', 'wb'))
        # PCA calculated successfully
        
        # calculate PCA
        ult_as_pca = ult_pca[n_pca].transform(ult['valid'])
        ult_rec = ult_pca[n_pca].inverse_transform(ult_as_pca)
        
        # measure loss
        loss = ((ult['valid'] - ult_rec) ** 2).mean()
        
        per_var = np.round(ult_pca[n_pca].explained_variance_ratio_ * 100, decimals=1)
        
        sum = 0
        if n_pca == 128:
            for i in range(n_pca):
                sum += per_var[i]
                print(i, sum)
        
        labels = ['PC' + str(x) for x in range(1, len(per_var) + 1)]
        plt.bar(x=range(1, len(per_var)+1), height=per_var, tick_label=labels)
        plt.ylabel('percentange of explained variance')
        plt.xlabel('principal component')
        plt.title('scree plot')
        # plt.show()
        plt.savefig(speaker + '_data/UTI_to_PCA_' + speaker + '_' + str(n_pca) + '.png')
        
        print('n_pca: ', n_pca, 'loss: ', loss)
    
    for percent in [0.5, 0.6, 0.7, 0.8, 0.9, 0.99]:
        ult_pca[percent] = PCA(n_components=percent, svd_solver='full')
        ult_pca[percent].fit(ult[train_valid])
        ult_as_pca = ult_pca[percent].transform(ult['valid'])
        print(percent, ult_pca[percent], ult_as_pca.shape)
        
   
'''
100 68.59999999999988
101 68.69999999999987
102 68.79999999999987
103 68.89999999999986
104 68.99999999999986
105 69.09999999999985
106 69.19999999999985
107 69.29999999999984
108 69.39999999999984
109 69.49999999999983
110 69.59999999999982
111 69.69999999999982
112 69.79999999999981
113 69.8999999999998
114 69.9999999999998
115 70.0999999999998
116 70.19999999999979
117 70.29999999999978
118 70.39999999999978
119 70.49999999999977
120 70.59999999999977
121 70.69999999999976
122 70.79999999999976
123 70.89999999999975
124 70.99999999999974
125 71.09999999999974
126 71.19999999999973
127 71.29999999999973
n_pca:  128 loss:  0.0023968221081565756
0.5 PCA(copy=True, iterated_power='auto', n_components=0.5, random_state=None,
  svd_solver='full', tol=0.0, whiten=False) (6379, 16)
0.6 PCA(copy=True, iterated_power='auto', n_components=0.6, random_state=None,
  svd_solver='full', tol=0.0, whiten=False) (6379, 43)
0.7 PCA(copy=True, iterated_power='auto', n_components=0.7, random_state=None,
  svd_solver='full', tol=0.0, whiten=False) (6379, 110)
0.8 PCA(copy=True, iterated_power='auto', n_components=0.8, random_state=None,
  svd_solver='full', tol=0.0, whiten=False) (6379, 280)
'''