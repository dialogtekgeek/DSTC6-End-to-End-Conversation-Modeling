#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Dialog corpus handler

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import re
import six
import numpy as np
from collections import Counter
import copy

def convert_words2ids(words, vocab, unk, sos=None, eos=None):
    """ convert word string sequence into word Id sequence 
        Args:
            words (list): word sequence
            vocab (dict): word-id mapping
            unk (int): id of unknown word <unk>
            sos (int): id of start-of-sentence symbol <sos>
            eos (int): id of end-of-sentence symbol <eos>
        Return:
            list of word Ids
    """
    word_ids = [ vocab[w] if w in vocab else unk for w in words ]
    if sos is not None:
        word_ids.insert(0,sos)
    if eos is not None:
        word_ids.append(eos)
    return np.array(word_ids, dtype=np.int32)


def get_vocabulary(textfile, initial_vocab={'<unk>':0,'<eos>':1}, vocabsize=0):
    """ acquire vocabulary from dialog text corpus 
        Args:
            textfile (str): filename of a dialog corpus
            initial_vocab (dict): initial word-id mapping
            vocabsize (int): upper bound of vocabulary size (0 means no limitation)
        Return:
            dict of word-id mapping
    """
    vocab = copy.copy(initial_vocab)
    word_count = Counter()
    for line in open(textfile,'r').readlines():
        for w in line.split()[1:]: # skip speaker indicator
            word_count[w] += 1

    # if vocabulary size is specified, most common words are selected
    if vocabsize > 0:
        for w in word_count.most_common(vocabsize):
            if w[0] not in vocab:
                vocab[w[0]] = len(vocab)
                if len(vocab) >= vocabsize:
                    break
    else: # all observed words are stored
        for w in word_count:
            if w not in vocab:
                vocab[w] = len(vocab)

    return vocab


def load(textfile, vocab, target):
    """ Load a dialog text corpus as word Id sequences
        Args:
            textfile (str): filename of a dialog corpus
            vocab (dict): word-id mapping
            target (str): target speaker name (e.g. 'S', 'Machine', ...) 
        Return:
            dict of word-id mapping
    """
    unk = vocab['<unk>']
    eos = vocab['<eos>']
    data = []
    dialog = []
    prev_speaker = ''
    prev_utterance = []
    input_utterance = []

    for line in open(textfile,'r').readlines():
        utterance = line.split()
        # store an utterance
        if len(utterance) > 0:
            speaker = utterance[0].split(':')[0] # get speaker name ('S: ...' -> 'S')
            if prev_speaker and prev_speaker != speaker:
                if prev_speaker == target:
                    # store the input-output pair for the target speaker
                    if len(input_utterance) > 0:
                        input_ids = convert_words2ids(input_utterance, vocab, unk)
                        output_ids = convert_words2ids(prev_utterance, vocab, unk, sos=eos, eos=eos)
                        dialog.append((input_ids, output_ids))
                        input_utterance = []
                    else:
                        # if the first utterance was given by system, it is included
                        # in input sequence
                        input_utterance = prev_utterance

                else: # all other speakers' utterances are used as input
                    input_utterance += prev_utterance

                prev_utterance = utterance[1:]
            else: # concatenate consecutive utterances by the same speaker
                prev_utterance += utterance[1:]

            prev_speaker = speaker

        # empty line represents the end of each dialog
        elif len(prev_utterance) > 0:
            # store the input-output pair for the target speaker
            if prev_speaker == target and len(input_utterance) > 0:
                input_ids = convert_words2ids(input_utterance, vocab, unk)
                output_ids = convert_words2ids(prev_utterance, vocab, unk, sos=eos, eos=eos)
                dialog.append((input_ids, output_ids))

            if len(dialog) > 0:
                data.append(dialog)

            dialog = []
            prev_speaker = ''
            prev_utterance = []
            input_utterance = []

    # store remaining utteraces if the file ends with EOF instead of an empty line
    if len(prev_utterance) > 0:
        # store the input-output pair for the target speaker
        if prev_speaker == target and len(input_utterance) > 0:
            input_ids = convert_words2ids(input_utterance, vocab, unk)
            output_ids = convert_words2ids(prev_utterance, vocab, unk, sos=eos, eos=eos)
            dialog.append((input_ids, output_ids))

        if len(dialog) > 0:
            data.append(dialog)
        
    return data


def make_minibatches(data, batchsize, max_length=0):
    """ Construct a mini-batch list of numpy arrays of dialog indices
        Args:
            data: dialog data read by load function.
            batchsize: dict of word-id mapping.
            max_length: if a mini-batch includes a word sequence that exceeds
                        this number, the batchsize is automatically reduced.
        Return:
            list of mini-batches (each batch is represented as a numpy array
            dialog ids).
    """
    if batchsize > 1:
        # sort dislogs by (#turns, max(reply #words, input #words))
        max_ulens = np.array([ max([(len(u[1]),len(u[0])) for u in d]) for d in data ])
        indices = sorted(range(len(data)), 
                      key=lambda i:(-len(data[i]), -max_ulens[i][0], -max_ulens[i][1]))
        # obtain partions of dialogs for diffrent numbers of turns
        partition = [0]
        prev_nturns = len(data[indices[0]])
        for k in six.moves.range(1,len(indices)):
            nturns = len(data[indices[k]])
            if prev_nturns > nturns:
                partition.append(k)
            prev_nturns = nturns

        partition.append(len(indices))
        # create mini-batch list
        batchlist = []
        for p in six.moves.range(len(partition)-1):
            bs = partition[p]
            while bs < partition[p+1]:
                # batchsize is reduced if max length in the mini batch 
                # is greater than 'max_length'
                be = min(bs + batchsize, partition[p+1])
                if max_length > 0:
                    max_ulen = np.max(max_ulens[bs:be])
                    be = min(be, bs + max(int(batchsize / (max_ulen / max_length + 1)), 1))

                batchlist.append(indices[bs:be])
                bs = be
    else:
        batchlist = [ np.array([i]) for i in six.moves.range(len(data)) ]

    return batchlist

