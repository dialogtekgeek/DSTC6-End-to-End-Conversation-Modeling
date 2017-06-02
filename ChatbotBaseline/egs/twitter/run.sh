#!/bin/bash

. path.sh

stage=1
use_slurm=false
slurm_queue=gpu_titanxp
#slurm_queue=test
workdir=`pwd`

## model definition
modeltype=lstm
vocabsize=20000
enc_layer=2
enc_esize=100
enc_hsize=512
dec_layer=2
dec_esize=100
dec_hsize=512
dec_psize=100

## optimization parameters
batch_size=100
max_batch_length=10
optimizer=Adam
dropout=0.5

# evaluation paramaters
beam=5
penalty=1.0
maxlen=30

# data files
train_data=./data/twitter_trial_data_train.txt
valid_data=./data/twitter_trial_data_dev.txt
eval_data=./data/twitter_trial_data_eval.txt

# get options
. utils/parse_options.sh || exit 1;

# directory setting
expdir=./exp/${modeltype}_${optimizer}_ee${enc_esize}_eh${enc_hsize}_de${dec_esize}_dh${dec_hsize}_dp${dec_psize}_bs${batch_size}_dr${dropout}

# command settings
if [ $use_slurm == true ]; then
  train_cmd="srun --job-name train --chdir=$workdir --gres=gpu:1 -p $slurm_queue"
  test_cmd="srun --job-name test --chdir=$workdir --gres=gpu:1 -p $slurm_queue"
  gpu_id=0
else
  train_cmd=""
  test_cmd=""
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
    echo scoring by BLEU metric
    tools/bleu_score.py ${expdir}/result_m${maxlen}_b${beam}_p${penalty}.txt \
    > ${expdir}/bleu_m${maxlen}_b${beam}_p${penalty}.txt
    cat ${expdir}/bleu_m${maxlen}_b${beam}_p${penalty}.txt
    echo stored in ${expdir}/bleu_m${maxlen}_b${beam}_p${penalty}.txt
fi
