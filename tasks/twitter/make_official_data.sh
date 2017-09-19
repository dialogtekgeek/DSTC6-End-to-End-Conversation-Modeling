#!/bin/bash

# you can change the directory path according to the location of stored data
stored_data=../../collect_twitter_dialogs/official_stored_data

# you need to download tweet ID info to specify the data sets
idfile=official_begin_end_ids.json
idlink=https://www.dropbox.com/s/8lmpu5dfw2hmpys/official_begin_end_ids.json.gz
echo downloading begin/end IDs for extracting data
wget $idlink
gunzip -f ${idfile}.gz

# extract train and dev sets
echo extracting training set
./extract_official_twitter_dialogs.py --data-dir $stored_data --id-file $idfile -t official_account_names_train.txt -o twitter_official_data_train.txt

echo extracting development set
./extract_official_twitter_dialogs.py --data-dir $stored_data --id-file $idfile -t official_account_names_dev.txt -o twitter_official_data_dev.txt

# extract 500 samples from dev set randomly for tentative evaluation
echo extracting test set
./utils/sample_dialogs.py twitter_official_data_dev.txt 500 > twitter_official_data_dev500.txt

echo done

echo checking data size
./utils/check_dialogs.py twitter_official_data_train.txt twitter_official_data_dev.txt

