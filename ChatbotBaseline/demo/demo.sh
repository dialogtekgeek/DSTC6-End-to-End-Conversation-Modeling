#!/bin/bash

# specify a model
model=../egs/twitter/exp/lstm_Adam_ee100_eh512_de100_dh512_dp100_bs100_dr0.5/conversation_model.best
gpu=`utils/get_available_gpu_id.sh`

# get options
. utils/parse_options.sh || exit 1;

tools/do_conversation.py -g $gpu $model

