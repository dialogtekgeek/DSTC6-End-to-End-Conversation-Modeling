# Baseline neural conversation model for DSTC6 (thori@merl.com)

This package includes training and evaluation scripts for neural conversation models
based on LSTM-based encoder decoder.
The scripts are written in python code, which were tested on python 2.7.6 and 3.4.3.
Some bash scripts are also used to run the python scripts.

## Requirements
Chainer <http://chainer.org> is used to perform neural network operations 
in the training and evaluation scripts.
So, you need to install the latest chainer (2.0) by
```
$ pip install chainer
```
In addtion, one NVIDIA GPU with 6GB or larger memory is necessary for runing 
the scripts in realistic time.  
CUDA 7.5 or higher with cuDNN 5.1 or higher is recommended.

The following python modules are required.

* cupy
* nltk
* tqdm

## Example tasks
We prepared two example tasks based on twitter and open subtitles.

### Twitter task
You can train and evaluate a conversation model by
```
$ cd egs/twitter
$ run.sh
```
where we assume that you have already generated the following dialog data files
in `../tasks/twitter`.

* `twitter_trial_data_train.txt`  (training data)
* `twitter_trial_data_dev.txt`    (development data for validation)
* `twitter_trial_data_eval.txt`   (test data for evaluation)

If you have not done yet, do `cd ../tasks/twitter` and `make_trial_data.sh`.

The directory of the dialog data can be changed by editing `CHATBOT_DATADIR` variable in file `path.sh` located in `egs/twitter`.  
Models and results will be stored in `egs/twitter/exp`

### OpenSubtiles task
You can train and evaluate a conversation model by
```
$ cd egs/opensubs
$ run.sh
```
where we assume that you have already generated the following dialog data files
in `../tasks/opensubs`.

* `opensubs_trial_data_train.txt`  (training data)
* `opensubs_trial_data_dev.txt`    (development data for validation)
* `opensubs_trial_data_eval.txt`   (test data for evaluation)

If you have not done yet, do `cd ../tasks/opensubs` and `make_trial_data.sh`.

The directory of the dialog data can be changed by editing `CHATBOT_DATADIR` variable in file `path.sh` located in `egs/opensubs`.
Models and results will be stored in `egs/opensubs/exp`

## Interactive demo
We also prepared an interactive demo `demo.sh` in directory `demo`.
With this demo, you can input text as a user, and a trained model will respond to you as an agent.

Sample models can be downloaded from 
`https://www.dropbox.com/s/6jfpxfh3aakjvts/sample_twitter_models.tgz` 

So you can obtain the model files as
```
$ cd demo
$ wget https://www.dropbox.com/s/6jfpxfh3aakjvts/sample_twitter_models.tgz
$ tar zxvf sample_twitter_models.tgz
```
In the directory `sample_twitter_models`, there are two files, one is for python2 and the other is for python3.
If you are using python3, `sample_twitter_models/sample_twitter_model_py3.best` is available for the demo.

The demo script can be executed as follows.
```
$ demo.sh --model sample_twitter_models/sample_twitter_model_py3.best
--- do neural conversations ------
Loading model params from sample_twitter_models/sample_twitter_model_py3.best
vocabulary size = 20000
--- start conversation [push Cntl-D to exit] ------
U: hello!
S: hi <USER> ! how can we help you today ?
U: i am thinking about buying a new car.
S: we can help you out with that ! what features are you looking for in your new car ?
U: i am looking for a minivan.
S: we 'd be happy to help you find one ! what 's your budget ?
U: about 30000 dollars. do you have such minivans?
S: <URL>
U: okay, i will check that. thank you.
S: you 're welcome . have a great day .
U:
```

## Directories and files
* README.md : This file
* demo : iteractive demo with a trained model
* egs : example tasks
* tools : python scripts for training and testing
* utils : some useful scripts

