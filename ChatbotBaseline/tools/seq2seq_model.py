# -*- coding: utf-8 -*-
"""Sequence-to-sequence model module

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import six
import chainer
import chainer.functions as F
from chainer import cuda
import numpy as np

class Sequence2SequenceModel(chainer.Chain):

    def __init__(self, encoder, decoder):
        """ Define model structure
            Args:
                encoder (~chainer.Chain): encoder network 
                decoder (~chainer.Chain): decoder network
        """
        super(Sequence2SequenceModel, self).__init__(
            encoder = encoder,
            decoder = decoder
        )


    def loss(self,es,x,y,t):
        """ Forward propagation and loss calculation
            Args:
                es (pair of ~chainer.Variable): encoder state 
                x (list of ~chainer.Variable): list of input sequences
                y (list of ~chainer.Variable): list of output sequences
                t (list of ~chainer.Variable): list of target sequences
                                   if t is None, it returns only states
            Return:
                es (pair of ~chainer.Variable(s)): encoder state
                ds (pair of ~chainer.Variable(s)): decoder state
                loss (~chainer.Variable) : cross-entropy loss
        """
        es,ey = self.encoder(es,x)
        ds,dy = self.decoder(es,y)
        if t is not None:
            loss = F.softmax_cross_entropy(dy,t)
            # avoid NaN gradients (See: https://github.com/pfnet/chainer/issues/2505)
            if chainer.config.train:
                loss += F.sum(F.concat(ey, axis=0)) * 0
            return es, ds, loss
        else: # if target is None, it only returns states
            return es, ds


    def generate(self, es, x, sos, eos, unk=0, maxlen=100, beam=5, penalty=1.0, nbest=1):
        """ Generate sequence using beam search 
            Args:
                es (pair of ~chainer.Variable(s)): encoder state 
                x (list of ~chainer.Variable): list of input sequences
                sos (int): id number of start-of-sentence label
                eos (int): id number of end-of-sentence label
                unk (int): id number of unknown-word label
                maxlen (int): list of target sequences
                beam (int): list of target sequences
                penalty (float): penalty added to log probabilities 
                                 of each output label.
                nbest (int): number of n-best hypotheses to be output
            Return:
                list of tuples (hyp, score): n-best hypothesis list
                 - hyp (list): generated word Id sequence
                 - score (float): hypothesis score
                pair of ~chainer.Variable(s)): decoder state of best hypothesis
        """
        # encoder
        es,ey = self.encoder(es, [x])
        # beam search
        ds = self.decoder.initialize(es, ey, sos)
        hyplist = [([], 0., ds)]
        best_state = None
        comp_hyplist = []
        for l in six.moves.range(maxlen):
            new_hyplist = []
            argmin = 0
            for out,lp,st in hyplist:
                logp = self.decoder.predict(st)
                lp_vec = cuda.to_cpu(logp.data[0]) + lp
                if l > 0:
                    new_lp = lp_vec[eos] + penalty * (len(out)+1)
                    new_st = self.decoder.update(st,eos)
                    comp_hyplist.append((out, new_lp))
                    if best_state is None or best_state[0] < new_lp:
                        best_state = (new_lp, new_st)

                for o in np.argsort(lp_vec)[::-1]:
                    if o == unk or o == eos:# exclude <unk> and <eos>
                        continue
                    new_lp = lp_vec[o]
                    if len(new_hyplist) == beam:
                        if new_hyplist[argmin][1] < new_lp:
                            new_st = self.decoder.update(st, o)
                            new_hyplist[argmin] = (out+[o], new_lp, new_st)
                            argmin = min(enumerate(new_hyplist), key=lambda h:h[1][1])[0] 
                        else:
                            break
                    else:
                        new_st = self.decoder.update(st, o)
                        new_hyplist.append((out+[o], new_lp, new_st))
                        if len(new_hyplist) == beam:
                            argmin = min(enumerate(new_hyplist), key=lambda h:h[1][1])[0] 

            hyplist = new_hyplist

        if len(comp_hyplist) > 0:
            maxhyps = sorted(comp_hyplist, key=lambda h:-h[1])[:nbest]
            return maxhyps, best_state[1]
        else:
            return [([],0)],None

