#!/bin/bash

## read path variables needed for the experiment
# edit ./path.sh according to your environment
. path.sh

## configuration for the experiment
# the following variables can be changed by options like
# run.sh --<variable_name> value ...
#  e.g. run.sh --stage 2
#
stage=1  # 1 start from training
         # 2 start from evaluation
         # 3 start from scoring

use_slurm=false # set true if send this job to slurm
slurm_queue=gpu_titanxp  # slurm queue name

workdir=`pwd`  # default working directory

## definition of model structure
modeltype=lstm
vocabsize=20000 # set vocabulary size (use most common words)
enc_layer=2     # number of encoder layers
enc_esize=100   # number of dimensions in encoder's word embedding layer
enc_hsize=512   # number of hidden units in each encoder layer
dec_layer=2     # number of decoder layers (should be the same as enc_layer)
dec_esize=100   # number of dimensions in decoder's word embedding layer
dec_hsize=512   # number of hidden units in each decoder layer
                # (should be the same as enc_hsize)
dec_psize=100   # number of dimesnions in decoder's projection layer before softmax

## optimization parameters
batch_size=100       # make mini-batches with 100 sequences
max_batch_length=10  # batch size is automatically reduced if the seuence length
                     # exceeds this number in each minibatch.
optimizer=Adam       # specify an optimizer
dropout=0.5          # set a dropout ratio

## evaluation paramaters
beam=5       # beam width for the beam search
penalty=1.0  # penalty added to log-probability of each word
             # a larger penalty means to generate longer sentences.
maxlen=30    # maxmum sequence length to be searched

## data files
train_data=${CHATBOT_DATADIR}/twitter_trial_data_train.txt
valid_data=${CHATBOT_DATADIR}/twitter_trial_data_dev.txt
eval_data=${CHATBOT_DATADIR}/twitter_trial_data_eval.txt

## get options (change the above variables with command line options)
. utils/parse_options.sh || exit 1;

## output directory (models and results will be stored in this directory)
expdir=./exp/${modeltype}_${optimizer}_ee${enc_esize}_eh${enc_hsize}_de${dec_esize}_dh${dec_hsize}_dp${dec_psize}_bs${batch_size}_dr${dropout}

## command settings
# if 'use_slurm' is true, it throws jobs to the specified queue of slurm
if [ $use_slurm == true ]; then
  train_cmd="srun --job-name train --chdir=$workdir --gres=gpu:1 -p $slurm_queue"
  test_cmd="srun --job-name test --chdir=$workdir --gres=gpu:1 -p $slurm_queue"
  gpu_id=0
else
  train_cmd=""
  test_cmd=""
  # get a GPU device id with the lowest memory consumption at this moment
  gpu_id=`utils/get_available_gpu_id.sh`
fi

# Set bash to 'debug' mode, it will exit on :
# -e 'error', -u 'undefined variable', -o ... 'error in pipeline', -x 'print commands',
set -e
set -u
set -o pipefail
#set -x

mkdir -p $expdir

# training
if [ $stage -le 1 ]; then
    # This script creates model files as '${expdir}/conversation_model.<epoch_number>'
    # where <epoch_number> indicates the epoch number of the trained model.
    # A symbolic link will be made to the best model for the validation data
    # as '${expdir}/conversation_model.best'
    echo start training
    $train_cmd tools/train_conversation_model.py \
      --gpu $gpu_id \
      --optimizer $optimizer \
      --train $train_data \
      --valid $valid_data \
      --batch-size ${batch_size} \
      --max-batch-length $max_batch_length \
      --vocab-size $vocabsize \
      --model ${expdir}/conversation_model \
      --snapshot ${expdir}/snapshot.pkl \
      --enc-layer $enc_layer \
      --enc-esize $enc_esize \
      --enc-hsize $enc_hsize \
      --dec-layer $dec_layer \
      --dec-esize $dec_esize \
      --dec-hsize $dec_hsize \
      --dec-psize $dec_psize \
      --dropout $dropout \
      --logfile ${expdir}/train.log
fi

# evaluation
if [ $stage -le 2 ]; then
    # This script generates sentences for evaluation data using
    # a model file '${expdir}/conversation_model.best'
    # the generated sentences will be stored in a file:
    # '${expdir}/result_m${maxlen}_b${beam}_p${penalty}.txt'
    echo start sentence generation
    $test_cmd tools/evaluate_conversation_model.py \
      --gpu $gpu_id \
      --test $eval_data \
      --model ${expdir}/conversation_model.best \
      --beam $beam \
      --maxlen $maxlen \
      --penalty $penalty \
      --output ${expdir}/result_m${maxlen}_b${beam}_p${penalty}.txt \
      --logfile ${expdir}/evaluate_m${maxlen}_b${beam}_p${penalty}.log
fi

# scoring
if [ $stage -le 3 ]; then
    # This script computes BLEU scores for the generated sentences in
    # '${expdir}/result_m${maxlen}_b${beam}_p${penalty}.txt'
    # the BLEU scores will be written in
    # '${expdir}/bleu_m${maxlen}_b${beam}_p${penalty}.txt'
    echo scoring by BLEU metric
    tools/bleu_score.py ${expdir}/result_m${maxlen}_b${beam}_p${penalty}.txt \
    > ${expdir}/bleu_m${maxlen}_b${beam}_p${penalty}.txt
    cat ${expdir}/bleu_m${maxlen}_b${beam}_p${penalty}.txt
    echo stored in ${expdir}/bleu_m${maxlen}_b${beam}_p${penalty}.txt
fi
