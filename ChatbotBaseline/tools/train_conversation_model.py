#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Train an encoder-decoder model for neural conversation

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import argparse
import math
import sys
import time
import random
import os
import copy

import numpy as np
import six

import chainer
from chainer import cuda
from chainer import optimizers
import chainer.functions as F
import pickle
import logging
import tqdm_logging
from tqdm import tqdm

from lstm_encoder import LSTMEncoder
from lstm_decoder import LSTMDecoder
from seq2seq_model import Sequence2SequenceModel

import dialog_corpus

# user the root logger
logger = logging.getLogger("root")

# training status and report
class Status:
    def __init__(self, interval, progress_bar=True):
        self.interval = interval
        self.loss = 0.
        self.cur_at = time.time()
        self.nsamples = 0
        self.count = 0
        self.progress_bar = progress_bar
        self.min_validate_ppl = 1.0e+10
        self.bestmodel_num = 1
        self.epoch = 1

    def update(self, loss, nsamples):
        self.loss += loss
        self.nsamples += nsamples
        self.count += 1
        if self.count % self.interval == 0:
            now = time.time()
            throuput = self.interval / (now - self.cur_at)
            perp = math.exp(self.loss / self.nsamples)
            logger.info('iter %d training perplexity: %.2f (%.2f iters/sec)' 
                        % (self.count, perp, throuput))
            self.loss = 0.
            self.nsamples = 0
            self.cur_at = now

    def new_epoch(self, validate_time=0):
        self.epoch += 1
        self.cur_at += validate_time # skip validation and model I/O time


# Traning routine
def train_step(model, optimizer, dataset, batchset, status, xp):
    chainer.config.train = True
    train_loss = 0.
    train_nsamples = 0

    num_interacts = sum([len(dataset[idx[0]]) for idx in batchset])
    if status.progress_bar:
        progress = tqdm(total=num_interacts)
        progress.set_description("Epoch %d" % status.epoch)

    for i in six.moves.range(len(batchset)):
        ds = None
        for j in six.moves.range(len(dataset[batchset[i][0]])):
            # prepare input, output, and target
            x = [ chainer.Variable(xp.asarray(dataset[k][j][0])) for k in batchset[i] ]
            y = [ chainer.Variable(xp.asarray(dataset[k][j][1][:-1])) for k in batchset[i] ]
            t = chainer.Variable(xp.asarray(np.concatenate( [dataset[k][j][1][1:] 
                                        for k in batchset[i]] )))
            # compute training loss
            ds,es,loss = model.loss(ds,x,y,t)
            train_loss += loss.data * len(t.data)
            train_nsamples += len(t.data)
            status.update(loss.data * len(t.data), len(t.data))
            # backprop
            model.cleargrads()
            loss.backward()
            loss.unchain_backward()  # truncate
            # update
            optimizer.update()
            if status.progress_bar:
                progress.update(1)

    if status.progress_bar:
        progress.close()

    return math.exp(train_loss/train_nsamples)


# Validation routine
def validate_step(model, dataset, batchset, status, xp):
    chainer.config.train = False
    validate_loss = 0.
    validate_nsamples = 0
    num_interacts = sum([len(dataset[idx[0]]) for idx in batchset])
    if status.progress_bar:
        progress = tqdm(total=num_interacts)
        progress.set_description("Epoch %d" % status.epoch)

    for i in six.moves.range(len(batchset)):
        ds = None
        for j in six.moves.range(len(dataset[batchset[i][0]])):
            # prepare input, output, and target
            x = [ chainer.Variable(xp.asarray(dataset[k][j][0])) for k in batchset[i] ]
            y = [ chainer.Variable(xp.asarray(dataset[k][j][1][:-1]))
                                        for k in batchset[i] ]
            t = chainer.Variable(xp.asarray(np.concatenate( [dataset[k][j][1][1:] 
                                        for k in batchset[i]] )))
            # compute validation loss
            es,ds,loss = model.loss(ds, x, y, t)

            # accumulate
            validate_loss += loss.data * len(t.data)
            validate_nsamples += len(t.data)
            if status.progress_bar:
                progress.update(1)

    if status.progress_bar:
        progress.close()

    return math.exp(validate_loss/validate_nsamples)


##################################
# main
def main():
    parser = argparse.ArgumentParser()
    # logging
    parser.add_argument('--logfile', '-l', default='', type=str,
                        help='write log data into a file')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='run in debug mode')
    parser.add_argument('--silent', '-s', action='store_true',
                        help='run in silent mode')
    parser.add_argument('--no-progress-bar', action='store_true',
                        help='hide progress bar')
    # train and validate data
    parser.add_argument('--train', default='train.txt', type=str,
                        help='set filename of training data')
    parser.add_argument('--validate', default='dev.txt', type=str,
                        help='set filename of validation data')
    parser.add_argument('--vocab-size', '-V', default=0, type=int,
                        help='set vocabulary size (0 means no limitation)')
    parser.add_argument('--target-speaker', '-T', default='S', 
                        help='set target speaker name to be learned for system output')
    # file settings
    parser.add_argument('--initial-model', '-i', 
                        help='start training from an initial model')
    parser.add_argument('--model', '-m', required=True,
                        help='set prefix of output model files')
    parser.add_argument('--resume', action='store_true', 
                        help='resume training from a previously saved snapshot')
    parser.add_argument('--snapshot', type=str,
                        help='dump a snapshot to a file after each epoch')
    # Model structure
    parser.add_argument('--enc-layer', default=2, type=int,
                        help='number of encoder layers')
    parser.add_argument('--enc-esize', default=100, type=int,
                        help='number of encoder input-embedding units')
    parser.add_argument('--enc-hsize', default=512, type=int,
                        help='number of encoder hidden units')

    parser.add_argument('--dec-layer', default=2, type=int,
                        help='number of decoder layers')
    parser.add_argument('--dec-esize', default=100, type=int,
                        help='number of decoder input-embedding units')
    parser.add_argument('--dec-hsize', default=512, type=int,
                        help='number of decoder hidden units')
    parser.add_argument('--dec-psize', default=100, type=int,
                        help='number of decoder pre-output projection units')
    # training conditions
    parser.add_argument('--optimizer', default='Adam', type=str, 
                        help="set optimizer (SGD, Adam, AdaDelta, RMSprop, ...)")
    parser.add_argument('--L2-weight', default=0.0, type=float,
                        help="set weight for L2-regularization term")
    parser.add_argument('--clip-grads', default=5., type=float,
                        help="set gradient clipping threshold")
    parser.add_argument('--dropout-rate', default=0.5, type=float,
                        help="set dropout rate in training")
    parser.add_argument('--num-epochs', '-e', default=20, type=int,
                        help='number of epochs to be trained')
    parser.add_argument('--learn-rate', '-R', default=1.0, type=float,
                        help='set initial learning rate for SGD')
    parser.add_argument('--learn-decay', default=1.0, type=float,
                        help='set decaying ratio of learning rate or epsilon')
    parser.add_argument('--lower-bound', default=1e-16, type=float,
                        help='set threshold of learning rate or epsilon for early stopping')
    parser.add_argument('--batch-size', '-b', default=50, type=int,
                        help='set batch size for training and validation')
    parser.add_argument('--max-batch-length', default=20, type=int,
                        help='set maximum sequence length to control batch size')
    parser.add_argument('--seed', default=99, type=int,
                        help='set a seed for random numbers')
    # select a GPU device
    parser.add_argument('--gpu', '-g', default=0, type=int,
                        help='GPU ID (negative value indicates CPU)')

    args = parser.parse_args()

    # flush stdout
    if six.PY2:
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
    # set up the logger
    tqdm_logging.config(logger, args.logfile, mode=('a' if args.resume else 'w'),
                        silent=args.silent, debug=args.debug)
    # gpu setup
    if args.gpu >= 0:
        cuda.check_cuda_available()
        cuda.get_device(args.gpu).use()
        xp = cuda.cupy
        xp.random.seed(args.seed)
    else:
        xp = np

    # randomize
    np.random.seed(args.seed)
    random.seed(args.seed)

    logger.info('----------------------------------')
    logger.info('Train a neural conversation model')
    logger.info('----------------------------------')
    if args.resume:
        if not args.snapshot:
            logger.error('snapshot file is not spacified.')
            sys.exit()

        with open(args.snapshot, 'rb') as f:
            vocab, optimizer, status, args = pickle.load(f)
        logger.info('Resume training from epoch %d' % status.epoch)
        logger.info('Args ' + str(args))
        model = optimizer.target
    else:    
        logger.info('Args ' + str(args))
        # Prepare RNN model and load data
        if args.initial_model:
            logger.info('Loading a model from ' + args.initial_model)
            with open(args.initial_model, 'rb') as f:
                vocab, model, tmp_args = pickle.load(f)
            status.cur_at = time.time()
        else:
            logger.info('Making vocabulary from ' + args.train)
            vocab = dialog_corpus.get_vocabulary(args.train, vocabsize=args.vocab_size)
            model = Sequence2SequenceModel(
                   LSTMEncoder(args.enc_layer, len(vocab), args.enc_hsize, 
                              args.enc_esize, dropout=args.dropout_rate),
                   LSTMDecoder(args.dec_layer, len(vocab), len(vocab),
                              args.dec_esize, args.dec_hsize, args.dec_psize,
                              dropout=args.dropout_rate))
        # Setup optimizer
        optimizer = vars(optimizers)[args.optimizer]()
        if args.optimizer == 'SGD':
            optimizer.lr = args.learn_rate
        optimizer.use_cleargrads()
        optimizer.setup(model)
        optimizer.add_hook(chainer.optimizer.GradientClipping(args.clip_grads))
        if args.L2_weight > 0.:
            optimizer.add_hook(chainer.optimizer.WeightDecay(args.L2_weight))
        status = None

    logger.info('Loading text data from ' + args.train)
    train_set = dialog_corpus.load(args.train, vocab, args.target_speaker)
    logger.info('Loading validation data from ' + args.validate)
    validate_set = dialog_corpus.load(args.validate, vocab, args.target_speaker)
    logger.info('Making mini batches')
    train_batchset = dialog_corpus.make_minibatches(train_set, batchsize=args.batch_size, max_length=args.max_batch_length)
    validate_batchset = dialog_corpus.make_minibatches(validate_set, batchsize=args.batch_size, max_length=args.max_batch_length)
    # report data summary
    logger.info('vocabulary size = %d' % len(vocab))
    logger.info('#train sample = %d  #mini-batch = %d' % (len(train_set), len(train_batchset)))
    logger.info('#validate sample = %d  #mini-batch = %d' % (len(validate_set), len(validate_batchset)))
    random.shuffle(train_batchset, random.random)

    # initialize status parameters
    if status is None:
        status = Status(max(round(len(train_batchset),-3)/50,500), 
                        progress_bar=not args.no_progress_bar)
    else:
        status.progress_bar = not args.no_progress_bar

    # move model to gpu
    if args.gpu >= 0:
        model.to_gpu()

    while status.epoch <= args.num_epochs:
        logger.info('---------------------training--------------------------')
        if args.optimizer == 'SGD':
            logger.info('Epoch %d : SGD learning rate = %g' % (status.epoch, optimizer.lr))
        else:
            logger.info('Epoch %d : %s eps = %g' % (status.epoch, args.optimizer, optimizer.eps))
        train_ppl = train_step(model, optimizer, train_set, train_batchset, status, xp)
        logger.info("epoch %d training perplexity: %f" % (status.epoch, train_ppl))
        # write the model params
        modelfile = args.model + '.' + str(status.epoch)
        logger.info('writing model params to ' + modelfile)
        model.to_cpu()
        with open(modelfile, 'wb') as f:
            pickle.dump((vocab, model, args), f, -1)
        if args.gpu >= 0:
            model.to_gpu()

        # start validation step
        logger.info('---------------------validation------------------------')
        start_at = time.time()
        validate_ppl = validate_step(model, validate_set, validate_batchset, status, xp)
        logger.info('epoch %d validation perplexity: %.4f' % (status.epoch, validate_ppl))
        # update best model with the minimum perplexity
        if status.min_validate_ppl >= validate_ppl:
            status.bestmodel_num = status.epoch
            logger.info('validation perplexity reduced: %.4f -> %.4f' % (status.min_validate_ppl, validate_ppl))
            status.min_validate_ppl = validate_ppl

        elif args.optimizer == 'SGD':
            modelfile = args.model + '.' + str(status.bestmodel_num)
            logger.info('reloading model params from ' + modelfile)
            with open(modelfile, 'rb') as f:
                vocab, model, tmp_args = pickle.load(f)
            if args.gpu >= 0:
                model.to_gpu()
            optimizer.lr *= args.learn_decay
            if optimizer.lr < args.lower_bound:
                break
            optimizer.setup(model)
        else:
            optimizer.eps *= args.learn_decay
            if optimizer.eps < args.lower_bound:
                break

        status.new_epoch(validate_time = time.time() - start_at)
        # dump snapshot
        if args.snapshot:
            logger.info('writing snapshot to ' + args.snapshot)
            model.to_cpu()
            with open(args.snapshot, 'wb') as f:
                pickle.dump((vocab, optimizer, status, args), f, -1)
            if args.gpu >= 0:
                model.to_gpu()
    
    logger.info('----------------')
    # make a symbolic link to the best model
    logger.info('the best model is %s.%d.' % (args.model,status.bestmodel_num))
    logger.info('a symbolic link is made as ' + args.model+'.best')
    if os.path.exists(args.model+'.best'):
        os.remove(args.model+'.best')
    os.symlink(os.path.basename(args.model+'.'+str(status.bestmodel_num)),
               args.model+'.best')
    logger.info('done')

if __name__ == "__main__":
    main()

