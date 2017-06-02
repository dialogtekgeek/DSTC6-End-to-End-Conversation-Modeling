# Twitter task example for DSTC6 (thori@merl.com)

This example includes scripts to train and evaluate conversation models
with twitter data.

## Requirements
Chainer (http://chainer.org) is used to perform neural network operations 
in the training and evaluation scripts.
So, you need to install the latest chainer by ``pip install chainer''
In addtion, one GPU with 6GB or larger memory is necessary for runing 
the script in realistic time.

The following python modules are required to run some examples.

- nltk
- tqdm

## run an example
First put dialog data files

- trial_data_train.txt  (training data)
- trial_data_dev.txt    (development data used for validation)
- trial_data_eval.txt   (test data)

into directory ./data .
Modify path.sh as necessary, and execute run.sh.
The script will train a LSTM-based conversation model using
the training and development data, and evaluate it with 
the test data.

## Directories and files
- README.md : This file
- data : directory to put processed text data
- exp : trained model file, evaluation results and log files will be stored (automatically created).
- path.sh : path setting file
- run.sh : a sample script to train and evaluate the model
- tools : python scripts for training and testing (link to ../../tools)
- utils : some useful scripts (link to ../../utils)

