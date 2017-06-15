#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Evaluate an encoder-decoder model for neural conversation

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import argparse
import sys
import time
import os
import copy
import pickle

import numpy as np
import six

import chainer
from chainer import cuda
import chainer.functions as F
from chainer import optimizers
import dialog_corpus

from tqdm import tqdm
import logging
import tqdm_logging

# use the root logger
logger = logging.getLogger("root")

# Generate sentences
def generate_sentences(model, dataset, vocab, xp, vocabsize=None, outfile=None,
                      maxlen=20, beam=5, penalty=2.0, progress_bar=True):

    # use chainer in testing mode
    chainer.config.train = False

    vocablist = sorted(vocab.keys(), key=lambda s:vocab[s])
    if vocabsize:
        vocabsize = len(vocab)

    eos = vocab['<eos>']
    unk = vocab['<unk>']

    if progress_bar:
        progress = tqdm(total=len(dataset))
        progress.set_description('Eval')

    if outfile:
        fo = open(outfile,'w')

    result = []

    for i in six.moves.range(len(dataset)):
        logger.debug('---- Dialog[%d] ----' % i)
        # predict decoder state for the context
        ds = None
        for j in six.moves.range(len(dataset[i])-1):
            inp = [vocablist[w] for w in dataset[i][j][0]]
            out = [vocablist[w] for w in dataset[i][j][1][1:-1]]
            logger.debug('U: %s' % ' '.join(inp))
            logger.debug('S: %s' % ' '.join(out))
            if outfile:
                six.print_('U: %s' % ' '.join(inp), file=fo)
                six.print_('S: %s' % ' '.join(out), file=fo)

            x_data = np.copy(dataset[i][j][0])
            x_data[ x_data >= vocabsize ] = unk
            x = [ chainer.Variable(xp.asarray(x_data)) ]
            y = [ chainer.Variable(xp.asarray(dataset[i][j][1][:-1])) ]
            es,ds = model.loss(ds, x, y, None)

        # generate a sentence for the last input
        inp = [vocablist[w] for w in dataset[i][-1][0]]
        ref = [vocablist[w] for w in dataset[i][-1][1][1:-1]]
        logger.debug('U: %s' % ' '.join(inp))
        if outfile:
            six.print_('U: %s' % ' '.join(inp), file=fo)

        if len(ref) > 0:
            logger.debug('S_REF: %s' % ' '.join(ref))
            if outfile:
                six.print_('S_REF: %s' % ' '.join(ref), file=fo)

        x_data = np.copy(dataset[i][-1][0])
        x_data[ x_data >= vocabsize ] = unk
        x = chainer.Variable(xp.asarray(x_data))
        # generate a sentence:
        # model.generate() returns n-best list, which is a list of 
        # tuples as [ (word Id sequence, score), ... ] and 
        # also returns the best decoder state
        besthyps,_ = model.generate(ds, x, eos, eos, unk=unk,
                                 maxlen=maxlen, beam=beam, penalty=penalty, nbest=1)
        # write result
        hyp = [vocablist[w] for w in besthyps[0][0]]
        if outfile:
            six.print_('S_HYP: %s\n' % ' '.join(hyp), file=fo, flush=True)

        result.append(hyp)
        # for debugging
        logger.debug('S_HYP: %s' % ' '.join(hyp))
        logger.debug('Score: %f' % besthyps[0][1])
        # update progress bar
        if progress_bar:
            progress.update(1)

    if progress_bar:
        progress.close()

    if outfile:
        fo.close()

    return result


##################################
# main
if __name__ =="__main__":
    parser = argparse.ArgumentParser()
    # logging
    parser.add_argument('--logfile', '-l', default='', 
                        help='write log data into a file')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='run in debug mode')
    parser.add_argument('--silent', '-s', action='store_true',
                        help='run in silent mode')
    parser.add_argument('--no-progress-bar', action='store_true',
                        help='hide the progress bar')
    # files 
    parser.add_argument('--model', '-m', required=True,
                        help='set conversation model to be used')
    parser.add_argument('--test', required=True, 
                        help='set filename of test data')
    parser.add_argument('--output', '-o', default='', 
                        help='write system output into a file')
    parser.add_argument('--target-speaker', '-T', default='', 
                        help='set target speaker name for system output')
    # search parameters
    parser.add_argument('--beam', '-b', default=5, type=int,
                        help='set beam width')
    parser.add_argument('--penalty', '-p', default=2.0, type=float,
                        help='set insertion penalty')
    parser.add_argument('--maxlen', '-M', default=20, type=int,
                        help='set maximum sequence length in beam search')
    # select a GPU device
    parser.add_argument('--gpu', '-g', default=0, type=int,
                        help='GPU ID (negative value indicates CPU)')

    args = parser.parse_args()

    # flush stdout
    if six.PY2:
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    # set up the logger
    tqdm_logging.config(logger, args.logfile, silent=args.silent, debug=args.debug)

    # gpu setup
    if args.gpu >= 0:
        cuda.check_cuda_available()
        cuda.get_device(args.gpu).use()
        xp = cuda.cupy
    else:
        xp = np

    logger.info('------------------------------------')
    logger.info('Evaluate a neural conversation model')
    logger.info('------------------------------------')
    logger.info('Args ' + str(args)) 
    # Prepare RNN model and load data
    logger.info('Loading model params from ' + args.model)
    with open(args.model, 'rb') as f:
        vocab, model, train_args = pickle.load(f)
    if args.gpu >= 0:
        model.to_gpu()

    if args.target_speaker:
        target_speaker = args.target_speaker
    else:
        target_speaker = train_args.target_speaker

    # prepare test data
    logger.info('Loading test data from ' + args.test)
    new_vocab = dialog_corpus.get_vocabulary(args.test, initial_vocab=vocab)
    test_set = dialog_corpus.load(args.test, new_vocab, target_speaker)
    # report data summary
    logger.info('vocabulary size = %d (%d)' % (len(vocab),len(new_vocab)))
    logger.info('#test sample = %d' % len(test_set))
    # generate sentences
    logger.info('----- start sentence generation -----')
    start_time = time.time()
    result = generate_sentences(model, test_set, new_vocab, xp, 
                                vocabsize=len(vocab), outfile=args.output,
                                maxlen=args.maxlen,
                                beam=args.beam, penalty=args.penalty,
                                progress_bar=not args.no_progress_bar)
    logger.info('----- finished -----')
    logger.info('Number of dialogs: %d' % len(test_set))
    logger.info('Number of hypotheses: %d' % len(result))
    logger.info('Wall time: %f (sec)' % (time.time() - start_time))
    logger.info('----------------')
    logger.info('done')

