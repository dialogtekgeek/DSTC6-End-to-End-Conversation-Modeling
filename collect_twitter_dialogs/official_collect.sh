#!/bin/bash

target=official_account_names_for_dstc6.txt
datetime=`date +"%Y-%m-%d_%H-%M-%S"`
collect_twitter_dialogs.py -t $target -o ./official_stored_data -l ./official_collect_${datetime}.log 
