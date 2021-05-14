Download Merlin & txt+ult2wav
---------------

Step 1: git clone https://github.com/BME-SmartLab/txt-ult2wav

Install tools
-------------

Similarly to original Merlin

Single speaker training (txt2wav)
-----------------------

Please follow below steps:
 
Step 2: cd txt-ult2wav/egs/txt+ult2wav/ultrasuite_tal_txt2wav/ <br/>
Step 3: ./run_full_voice.sh <UltraSuite-TaL dir> <speaker> <br/>
e.g. ./run_full_voice.sh ~/UltraSuite-TaL/TaL80/core/ 01fi 

Generate new sentences
----------------------

To generate new sentences, please follow below steps:

Step 4: ./08_merlin_synthesis.sh <speaker>  <br/>

Citation
--------

If you publish work based on Merlin & txt+ult2wav, please cite: 

Implementation of Tamás Gábor Csapó, László Tóth, Gábor Gosztolya, Alexandra Markó, ,,Speech Synthesis from Text and Ultrasound Tongue Image-based Articulatory Input'', submitted to SSW11, 2021.