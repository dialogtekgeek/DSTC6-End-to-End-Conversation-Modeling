#!/bin/bash

# you can change the directory path according to the location of stored data
stored_data=../../collect_twitter_dialogs/official_stored_data

# tweet ID list of the test set
# (reference text is not provided, i.e., last turn of each dialog is empty)
idlist=official_testset_ids+refs.json
gunzip -c ${idlist}.gz > $idlist

echo extracting the official test set
extract_official_twitter_testset.py \
    --id-list $idlist \
    --data-dir $stored_data \
    --target official_account_names_test.txt \
    --output twitter_official_data_test+refs.txt

echo done
