#!/usr/bin/env python
"""Check sizes of extracted dialog data

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import sys

class dataset:
    def __init__(self, name, filename, n_dialogs, n_utters, n_words):
        self.name = name
        self.filename = filename
        self.n_dialogs = n_dialogs
        self.n_utters = n_utters
        self.n_words = n_words

    def check(self, n_dialogs, n_utters, n_words):
        print('--- %s set ---' % self.name)
        print('n_dialogs: %d (%.2f %% difference from reference: %d)' % (n_dialogs, float(abs(self.n_dialogs - n_dialogs))/n_dialogs*100, self.n_dialogs))
        print('n_utters: %d (%.2f %% difference from reference: %d)' % (n_utters, float(abs(self.n_utters - n_utters))/n_utters*100, self.n_utters))
        print('n_words: %d (%.2f %% difference from reference: %d)' % (n_words, float(abs(self.n_words - n_words))/n_words*100, self.n_words))


if __name__ == "__main__":
    #set data info (target sizes for official data sets)
    train_set = dataset('train', sys.argv[1], 888201, 2157389, 40073702)
    dev_set = dataset('dev', sys.argv[2], 107506, 262228, 4900743)

    for data in [train_set, dev_set]:
        n_utters = 0
        n_dialogs = 0
        n_words = 0
        for ln in open(data.filename,'r').readlines():
            tokens = ln.split()
            if len(tokens) > 0:
                n_words += len(tokens)-1
                n_utters += 1
            else:
                n_dialogs += 1

        data.check(n_dialogs, n_utters, n_words)
    print("----------------------------------------------------")
    print("If the data size differences are greater than 1%, ")
    print("please contact the track organizers (chori@merl.com, thori@merl.com)")
    print("with the above information.")
    print("----------------------------------------------------")
