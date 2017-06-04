#!/bin/bash

# you can download English data of OpenSubtitles2016 from
# 
# http://opus.lingfil.uu.se/download.php?f=OpenSubtitles2016/en.tar.gz
# 
# and extract xml files by
# 
# tar zxvf en.tar.gz
#
# you need to specify the location of the data
stored_data=./OpenSubtitles2016/xml/en

# extract train and dev sets
echo extracting training, development, and test sets
./extract_opensubs_dialogs.py \
   --output opensubs_trial_data_train.txt opensubs_trial_data_dev.txt \
   --ratio 0.1 0.001 \
   --rootdir $stored_data

echo extracting evaluation data
# extract 500 samples from dev set randomly for evaluation
./utils/sample_dialogs.py opensubs_trial_data_dev.txt 500 > opensubs_trial_data_eval.txt

echo done
