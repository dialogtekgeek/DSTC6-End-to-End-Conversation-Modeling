#!/bin/bash

target=account_names_for_dstc6.txt
datetime=`date +"%Y-%m-%d_%H-%M-%S"`
collect_twitter_dialogs.py -t $target -o ./stored_data -l ./collect_${datetime}.log 
