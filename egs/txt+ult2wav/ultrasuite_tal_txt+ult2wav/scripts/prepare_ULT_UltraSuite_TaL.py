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

n_pca = 128

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
if not os.path.isfile(speaker + '_data/UTI_to_PCA_' + speaker + '.sav'):
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
        
        if train_valid == 'train':
            print('calculating PCA...')
            ult_pca = PCA(n_components = n_pca)
            ult_pca.fit(ult[train_valid])
    
            pickle.dump(ult_pca, open(speaker + '_data/UTI_to_PCA_' + speaker + '.sav', 'wb'))
    # PCA calculated successfully

    # read ultrasound files, cut, calculate PCA, and interpolate them to 5 ms
    ult_pca = pickle.load(open(speaker + '_data/UTI_to_PCA_' + speaker + '.sav', 'rb'))

    for train_valid in ['train', 'valid', 'test']:
        
        for basefile in ult_files[train_valid]:
            print('starting PCA calculation for ', basefile)
            
            ult_data = read_ult(basefile + '.ult', n_lines, n_pixels)
            
            # skip first ultrasound image
            # ult_data = ult_data[1:]
            
            ult_data0 = np.empty((len(ult_data), n_lines, n_pixels_reduced))
            
            # resize
            for i in range(len(ult_data)):
                ult_data0[i] = skimage.transform.resize(ult_data[i], (n_lines, n_pixels_reduced), preserve_range=True) / 255
            
            # calculate PCA
            ult_as_pca = ult_pca.transform(ult_data0.reshape(-1, n_lines * n_pixels_reduced))
            
            # resample / interpolate ult data to 5 ms frameshift (from 81.5 fps = 12 ms)
            interpolate_ratio = hopLength_UTI / hopLength
            ult_as_pca = skimage.transform.resize(ult_as_pca, \
                (int(ult_as_pca.shape[0] * interpolate_ratio), ult_as_pca.shape[1]), preserve_range=True)
            
            ult_as_pca.astype('float32').tofile(basefile + '_cut_48k.ultpca128')
            