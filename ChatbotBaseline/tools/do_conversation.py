#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Interactive neural conversation demo

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import argparse
import sys
import os
import pickle
import re
import six
import numpy as np

import chainer
from chainer import cuda
from nltk.tokenize import casual_tokenize

##################################
# main
if __name__ =="__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--gpu', '-g', default=0, type=int,
                        help='GPU ID (negative value indicates CPU)')
    parser.add_argument('--beam', '-b', default=5, type=int,
                        help='set beam width')
    parser.add_argument('--penalty', '-p', default=1., type=float,
                        help='set insertion penalty')
    parser.add_argument('--nbest', '-n', default=1, type=int,
                        help='generate n-best sentences')
    parser.add_argument('--maxlen', default=20, type=int,
                        help='set maximum sequence length in beam search')
    parser.add_argument('model', nargs=1,
                        help='conversation model file')

    args = parser.parse_args()
    if args.gpu >= 0:
        cuda.check_cuda_available()
        cuda.get_device(args.gpu).use()
        xp = cuda.cupy
    else:
        xp = np

    # use chainer in testing mode 
    chainer.config.train = False

    # Prepare RNN model and load data
    print("--- do neural conversations ------")
    print('Loading model params from ' + args.model[0])
    with open(args.model[0], 'rb') as f:
        vocab, model, train_args = pickle.load(f)
    if args.gpu >= 0:
        model.to_gpu()
    # report data summary
    print('vocabulary size = %d' % len(vocab))
    vocablist = sorted(vocab.keys(), key=lambda s:vocab[s])
    # generate sentences
    print("--- start conversation [push Cntl-D to exit] ------")
    unk = vocab['<unk>']
    eos = vocab['<eos>']
    state = None
    while True:
        try:
            input_str = six.moves.input('U: ')
        except EOFError:
           break

        if input_str:
            if input_str=='exit' or input_str=='quit':
                break
            sentence = []
            for token in casual_tokenize(input_str, preserve_case=False, reduce_len=True):
                # make a space before apostrophe
                token = re.sub(r'^([a-z]+)\'([a-z]+)$','\\1 \'\\2',token)
                for w in token.split():
                    sentence.append(vocab[w] if w in vocab else unk)

            x_data = np.array(sentence, dtype=np.int32)
            x = chainer.Variable(xp.asarray(x_data))
            besthyps,state = model.generate(state, x, eos, eos, unk=unk, 
                                     maxlen=args.maxlen,
                                     beam=args.beam, 
                                     penalty=args.penalty,
                                     nbest=args.nbest)
            ## print sentence
            if args.nbest == 1:
                sys.stdout.write('S:')
                for w in besthyps[0][0]:
                    if w != eos:
                        sys.stdout.write(' ' + vocablist[w])
                sys.stdout.write('\n')
            else:    
                for n,s in enumerate(besthyps):
                    sys.stdout.write('S%d:' % n)
                    for w in s[0]:
                        if w != eos:
                            sys.stdout.write(' ' + vocablist[w])
                    sys.stdout.write(' (%f)' % s[1])
        else:
            print("--- start conversation [push Cntl-D to exit] ------")
            state = None

    print('done')

