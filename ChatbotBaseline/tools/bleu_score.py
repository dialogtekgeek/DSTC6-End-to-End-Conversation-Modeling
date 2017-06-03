#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""BLEU score for dialog system output

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import sys
from nltk.translate.bleu_score import corpus_bleu

refs = []
hyps = []
for utt in open(sys.argv[1],'r').readlines():
    if utt.startswith('S_REF:'):
        ref = utt.replace('S_REF:','').split()
        refs.append([ref])

    if utt.startswith('S_HYP:'): 
        hyp = utt.replace('S_HYP:','').split()
        hyps.append(hyp)

# obtain BLEU1-4
print("--------------------------------")
print("Evaluated file: " + sys.argv[1])
print("Number or references: %d" % len(refs))
print("Number or hypotheses: %d" % len(hyps))
print("--------------------------------")
if len(refs) > 0 and len(hyps) > 0 and len(refs)==len(hyps):
    result = []
    for n in [1,2,3,4]:
        weights = [1./n] * n
        print('Bleu%d: %f' % (n, corpus_bleu(refs,hyps,weights=weights)))
else:
    print("Error: mismatched references and hypotheses.")
print("--------------------------------")

