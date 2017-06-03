# Baseline neural conversation model for DSTC6 (thori@merl.com)

This package includes training and evaluation scripts for neural conversation models
based on LSTM-based encoder decoder.
The scripts are written in python code, which were tested on python 2.7.6 and 3.4.3.
Some bash scripts are also used to run the python scripts.

## Requirements
Chainer <http://chainer.org> is used to perform neural network operations 
in the training and evaluation scripts.
So, you need to install the latest chainer (2.0) by `pip install chainer`
In addtion, one NVIDIA GPU with 6GB or larger memory is necessary for runing 
the scripts in realistic time.  
CUDA 7.5 or higher with cuDNN is recommended.

The following python modules are required.

* cupy
* nltk
* tqdm

## Example tasks
We prepared two example tasks based on twitter and open subtitles.

### Twitter task
You can train and evaluate a conversation model by
```sh
cd egs/twitter
run.sh
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
```sh
cd egs/opensubs
run.sh
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
With this demo, you can input text as a user, and a trained model will respond to you.
if the trained model is `sample_twitter_model.best`, you can run as
```
$ cd demo
$ demo.sh --model sample_twitter_model.best
--- do neural conversations ------
Loading model params from ../egs/twitter/exp/lstm_Adam_ee100_eh512_de100_dh512_dp100_bs100_dr0.5/conversation_model.8
vocabulary size = 20000
--- start conversation [push Cntl-D to exit] ------
U: hello!
S: hi <USER> , how can we help you today ?
U: i am thinking about buying a new car.
S: we can help you out with that ! what features are you looking for in your new car ?
U: cool sports car!
S: thank you !
U: can you recommend such cars you have?
S: yes we do !
U: what do you have?
S: <URL>
U: okay, i understand ...
S: we 're sorry to hear that . please dm us your contact info so we can reach out .
U: okay, have a good day!
S: you too !
U:
```

## Directories and files
* README.md : This file
* demo : iteractive demo with a trained model
* egs : example tasks
* tools : python scripts for training and testing
* utils : some useful scripts

