# -*- coding: utf-8 -*-
"""LSTM Encoder

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import numpy as np
import chainer
from chainer import cuda
import chainer.links as L
import chainer.functions as F

class LSTMEncoder(chainer.Chain):

    def __init__(self, n_layers, in_size, out_size, embed_size, dropout=0.5):
        """Initialize encoder with structure parameters
        Args:
            n_layers (int): Number of layers.
            in_size (int): Dimensionality of input vectors.
            out_size (int) : Dimensionality of hidden vectors to be output.
            embed_size (int): Dimensionality of word embedding.
            dropout (float): Dropout ratio.
        """
        super(LSTMEncoder, self).__init__(
            embed = L.EmbedID(in_size, embed_size),
            lstm = L.NStepLSTM(n_layers, embed_size, out_size, dropout)
        )
        for param in self.params():
            param.data[...] = np.random.uniform(-0.1, 0.1, param.data.shape)


    def __call__(self, s, xs):
        """Calculate all hidden states and cell states.
        Args:
            s  (~chainer.Variable or None): Initial (hidden & cell) states. If ``None``
                is specified zero-vector is used.
            xs (list of ~chianer.Variable): List of input sequences.
                Each element ``xs[i]`` is a :class:`chainer.Variable` holding
                a sequence.
        Return:
            (hy,cy): a pair of hidden and cell states at the end of the sequence,
            ys: a hidden state sequence at the last layer
        """
        if len(xs) > 1:
            sections = np.cumsum(np.array([len(x) for x in xs[:-1]], dtype=np.int32))
            xs = F.split_axis(self.embed(F.concat(xs, axis=0)), sections, axis=0)
        else:
            xs = [ self.embed(xs[0]) ]
        if s is not None:
            hy, cy, ys = self.lstm(s[0], s[1], xs)
        else:
            hy, cy, ys = self.lstm(None, None, xs)

        return (hy,cy), ys

