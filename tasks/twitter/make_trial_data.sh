#!/bin/bash

# you can change the directory path according to the location of stored data
stored_data=../../collect_twitter_dialogs/stored_data

# extract train and dev sets
echo extracting training set
./extract_twitter_dialogs.py --data-dir $stored_data -t account_names_train.txt -o twitter_trial_data_train.txt
echo extracting development set
./extract_twitter_dialogs.py --data-dir $stored_data -t account_names_dev.txt -o twitter_trial_data_dev.txt

# extract 500 samples from dev set randomly for evaluation
echo extracting test set
./utils/sample_dialogs.py twitter_trial_data_dev.txt 500 > twitter_trial_data_eval.txt

echo done
