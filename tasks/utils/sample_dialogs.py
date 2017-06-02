#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import random
import six
import copy

dialogs = []
dialog = []
for ln in open(sys.argv[1], 'r').readlines():
    ln = ln.strip()
    if ln != '':
        dialog.append(ln)
        # partial dialogs are also included
        if len(dialog)>=2 and ln.startswith('S:'):
            dialogs.append(copy.copy(dialog))
    else:
        dialog = []

random.seed(99)
# 2nd argument is necessary for compatibility between python2.7~ and 3.2~
random.shuffle(dialogs, random.random) 
n_samples = int(sys.argv[2])

for i in six.moves.range(n_samples):
    for d in dialogs[i]:
        print(d)
    print('')

