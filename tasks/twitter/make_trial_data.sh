#!/bin/bash

# you can change the directory path according to the location of stored data
stored_data=../../collect_twitter_dialogs/stored_data

# extract train and dev sets
./extract_twitter_dialogs.py --data-dir $stored_data -t account_names_train.txt -o twitter_trial_data_train.txt
./extract_twitter_dialogs.py --data-dir $stored_data -t account_names_dev.txt -o twitter_trial_data_dev.txt
# extract 500 samples from dev set randomly for evaluation
./sample_dialogs.py data_dev.txt 500 > twitter_trial_data_eval.txt

