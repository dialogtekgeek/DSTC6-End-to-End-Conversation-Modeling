#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""extract_opensubs_dialogs.py:
   A script to extract text from OpenSubtitles.

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import xml.etree.ElementTree as ET
from gzip import GzipFile
import sys
import re
import glob
import random
from tqdm import tqdm
import six
import argparse

# regular expressions for cleaning up text
tag_re = re.compile(r'(<!--.*?-->|<[^>]*>|{[^}]*}|\([^\)]*\)|\[[^\]]*\])')
symbol_re = re.compile(u'([-–—]+$| [-–—]+|[-–—]+ |% %|#+|\'\'|``| \' |[\(\)\"])')
space_re = re.compile(r'\s+')
appos1_re = re.compile(r' \' (?=(em|im|s|t|bout|cause)\s+)')
appos2_re = re.compile(r'(?<=n) \' ')
title_re = re.compile(r'(?<=( mr| jr| ms| dr| st|mrs)) \.')
speaker_re = re.compile(r'^\s*[A-z]*\s*:')
ignore_re = re.compile(r'^(\s*|[\.\?$%!,:;])$')

def preprocess(sent):
    new_sent = tag_re.sub(' ', sent).replace('\\\'','\'').lower()
    new_sent = appos1_re.sub(' \'', new_sent)
    new_sent = appos2_re.sub('\' ', new_sent)
    new_sent = title_re.sub('. ', new_sent)
    new_sent = speaker_re.sub('', new_sent)
    new_sent = space_re.sub(' ', symbol_re.sub(' ', new_sent)).strip()
    if not ignore_re.match(new_sent):
        return new_sent.encode('utf-8')
    else:
        return '' 


def extract(filePath, corpus):
    """extract text from an XML file and tokenize it
    """
    if filePath.endswith('.gz'):
        tree = ET.parse(GzipFile(filename=filePath))
    else:
        tree = ET.parse(filePath)

    root = tree.getroot()
    sent = ''
    for child in root:
        for elem in child:
            if elem.tag == 'w':
                sent += ' ' + elem.text

        if not sent.strip().endswith(':'):
            new_sent = preprocess(sent)
            #six.print_('%s -> %s' % (sent.encode('utf-8'),new_sent))
            if new_sent:
                corpus.append((new_sent, len(new_sent.split())))
            sent = ''

    corpus.append(('',0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=['train.txt'], nargs='+', type=str,
                        help='Filenames of data')
    parser.add_argument('--ratio', default=[0.01], nargs='+', type=float,
                        help='Extraction rate for each data set')
    parser.add_argument('--max-length', default=20, type=float,
                        help='Maximum length of sentences')
    parser.add_argument('--rootdir', default='.',  
                        help='root directory of data source')

    args = parser.parse_args()

    if len(args.output) != len(args.ratio):
        raise Exception('The number of output files (%d) and the number extraction ratios (%d) should be the same.' % (len(args.output), len(args.partion)))

    rootdir = args.rootdir
    print('collecting files from ' + rootdir)
    xmlfiles = glob.glob(rootdir + '/*.xml.gz') + glob.glob(rootdir + '/*/*.xml.gz') + glob.glob(rootdir + '/*/*/*.xml.gz')

    random.shuffle(xmlfiles, random.random)
    total_ratio = sum(args.ratio)
    n_files = int( len(xmlfiles) * total_ratio )
    print('loading text from %d/%d files' % (n_files, len(xmlfiles)))
    corpus = []
    for n in tqdm(six.moves.range(n_files)):
        extract(xmlfiles[n], corpus)
   
    print('%d sentences loaded' % len(corpus))
    random.seed(1)
    indices = list(six.moves.range(len(corpus)-1))
    random.shuffle(indices, random.random)

    partition = [0]
    acc_ratio = 0.0
    for r in args.ratio:
        acc_ratio += r / total_ratio
        partition.append(int(acc_ratio * len(corpus)))

    for n in six.moves.range(len(partition)-1):
        print('writing %d sentence pairs to %s' % (partition[n+1]-partition[n], args.output[n]))
        with open(args.output[n],'w') as f:
            for idx in indices[partition[n]:partition[n+1]]:
                len1 = corpus[idx][1]
                len2 = corpus[idx+1][1]
                if 0 < len1 < args.max_length and 0 < len2 < args.max_length:
                    six.print_('U: %s\nS: %s\n' % (corpus[idx][0],corpus[idx+1][0]), file=f)
                
