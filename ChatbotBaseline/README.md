# Baseline neural conversation model for DSTC6 (thori@merl.com)

This package includes data preprocessing, training and evaluation scripts
for neural conversation models based on LSTM-based encoder decoder.
The scripts are written in python code, which were tested on python 2.7.6 and 3.4.3.
Some bash scripts are also used to run the python scripts.

## Requirements
Chainer (http://chainer.org) is used to perform neural network operations 
in the training and evaluation scripts.
So, you need to install the latest chainer by ``pip install chainer''
In addtion, one Nvidia GPU with 6GB or larger memory is necessary for runing 
the script in realistic time.

The following python modules are required to run some examples.

- nltk
- tqdm

## run examples
We prepared two example tasks based on twitter and open subtitles.
If you try the twitter task, go to directory egs/twitter and execute run.sh.
Before executing run.sh, you may need to modify path.sh in the directory.
The most import variable is DATADIR that indicates data source directory.

For the twitter task, you can specify it as:

export DATADIR=(SOME_DIRECTORY)/collect_twitter_dialogs/stored_data

where we assumes you collected twitter data using collect_twitter_dialogs
tools.

## Directories and files
- README.md : This file
- egs : example tasks
- tools : python scripts for training and testing
- utils : some useful scripts

