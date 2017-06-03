# -*- coding: utf-8 -*-
"""LSTM Decoder module

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import numpy as np
import chainer
from chainer import cuda
import chainer.links as L
import chainer.functions as F

class LSTMDecoder(chainer.Chain):

    def __init__(self, n_layers, in_size, out_size, embed_size, hidden_size, proj_size, dropout=0.5):
        """Initialize encoder with structure parameters

        Args:
            n_layers (int): Number of layers.
            in_size (int): Dimensionality of input vectors.
            out_size (int): Dimensionality of output vectors.
            embed_size (int): Dimensionality of word embedding.
            hidden_size (int) : Dimensionality of hidden vectors.
            proj_size (int) : Dimensionality of projection before softmax.
            dropout (float): Dropout ratio.
        """
        super(LSTMDecoder, self).__init__(
            embed = L.EmbedID(in_size, embed_size),
            lstm = L.NStepLSTM(n_layers, embed_size, hidden_size, dropout),
            proj = L.Linear(hidden_size, proj_size),
            out = L.Linear(proj_size, out_size)
        )
        self.dropout = dropout
        for param in self.params():
            param.data[...] = np.random.uniform(-0.1, 0.1, param.data.shape)


    def __call__(self, s, xs):
        """Calculate all hidden states, cell states, and output prediction.

        Args:
            s (~chainer.Variable or None): Initial (hidden, cell) states.  If ``None``
                is specified zero-vector is used.
            xs (list of ~chianer.Variable): List of input sequences.
                Each element ``xs[i]`` is a :class:`chainer.Variable` holding
                a sequence.
        Return:
            (hy,cy): a pair of hidden and cell states at the end of the sequence,
            y: a sequence of pre-activatin vectors at the output layer
 
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

        #y = self.out(F.tanh(self.proj(F.concat(ys, axis=0))))
        y = self.out(self.proj(
                F.dropout(F.concat(ys, axis=0), ratio=self.dropout)))
        return (hy,cy),y


    # interface for beam search
    def initialize(self, s, x, i):
        """Initialize decoder

        Args:
            s (any): Initial (hidden, cell) states.  If ``None`` is specified
                     zero-vector is used.
            x (~chainer.Variable or None): Input sequence
            i (int): input label.
        Return:
            initial decoder state
        """
        # LSTM decoder can be initialized in the same way as update()
        return self.update(s,i)


    def update(self, s, i):
        """Update decoder state

        Args:
            s (any): Current (hidden, cell) states.  If ``None`` is specified 
                     zero-vector is used.
            i (int): input label.
        Return:
            (~chainer.Variable) updated decoder state
        """
        if cuda.get_device_from_array(s[0].data).id >= 0:
            xp = cuda.cupy
        else:
            xp = np

        v = chainer.Variable(xp.array([i],dtype=np.int32))
        x = self.embed(v)
        if s is not None:
            hy, cy, dy = self.lstm(s[0], s[1], [x])
        else:
            hy, cy, dy = self.lstm(None, None, [x])

        return hy, cy, dy


    def predict(self, s):
        """Predict single-label log probabilities

        Args:
            s (any): Current (hidden, cell) states.
        Return:
            (~chainer.Variable) log softmax vector
        """
        y = self.out(self.proj(s[2][0]))
        return F.log_softmax(y)

