#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""extract_official_twitter_dialogs.py:
   A script to extract text from twitter dialogs.

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import json
import sys
import os
import six
import re
import argparse
from datetime import datetime
from tqdm import tqdm
from nltk.tokenize import casual_tokenize

if six.PY2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

def preprocess(text, name, speaker='U', first_name=None):
    """ normalize and tokenize raw text 
    args:
        text: input raw text (str)
        name: user name (str)
        first_name: user's first name (str)
        sys_utt: flag if this is a sysmtem's turn (bool)
    return:
        normalized text (str)
    """
    # modify apostrophe character
    text = re.sub(u'’',"'",text)
    text = re.sub(u'(“|”)','',text)
    # remove handle names in the beginning
    text = re.sub(r'^(@[A-Za-z0-9_]+[\.;, ])+','',text)
    # remove connected tweets indicator e.g. (1/2) (2/2)
    text = re.sub(r'(^|[\(\[ ])[1234]\/[2345]([\)\] ]|$)',' ',text)
    # replace long numbers
    text = re.sub(r'(?<=[ A-Z])(\+\d|\d\-|\d\d\d+|\(\d\d+\))[\d\- ]+\d\d\d','<NUMBERS>',text)
    # replace user name in system response
    if speaker == 'S':
        if name:
            text = re.sub('@'+name, '<USER>', text)
        if first_name:
            text = re.sub('(^|[^A-Za-z0-9])'+first_name+'($|[^A-Za-z0-9])', '\\1<USER>\\2', text)

    # tokenize and replace entities
    words = casual_tokenize(text, preserve_case=False,reduce_len=True)
    for n in six.moves.range(len(words)):
        token = words[n]
        # replace entities with tags (E-MAIL, URL, NUMBERS, USER, etc)
        token = re.sub(r'^([a-z0-9_\.\-]+@[a-z0-9_\.\-]+\.[a-z]+)$','<E-MAIL>',token)
        token = re.sub(r'^https?:\S+$','<URL>',token)
        token = re.sub('^<numbers>$','<NUMBERS>',token)
        token = re.sub('^<user>$','<USER>',token)
        # make spaces for apostrophe and period
        token = re.sub(r'^([a-z]+)\'([a-z]+)$','\\1 \'\\2',token)
        token = re.sub(r'^([a-z]+)\.([a-z]+)$','\\1 . \\2',token)
        words[n] = token
    # join
    text = ' '.join(words)
    # remove signature of tweets (e.g. ... ^TH, - John, etc.)
    if speaker == 'S':
        text = re.sub(u'[\\^\\-~–][\\-– ]*([a-z]+\\s*|[a-z ]{2,8})(<URL>\\s*$|\\.\\s*$|$)','\\2',text)
        if not re.search(r' (thanks|thnks|thx)\s*$', text):
            text = re.sub(u'(?<= [\\-,!?.–])\\s*[a-z]+\\s*$','',text)

    return text


if __name__ == "__main__":
    # parse command line
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target', help='read screen names from a file')
    parser.add_argument('-o', '--output', help='output processed text into a file')
    parser.add_argument('-d', '--debug', action='store_true', help='debug mode')
    parser.add_argument('--data-dir', help='specify data directory')
    parser.add_argument('--id-list', required=True, help='use ID list file')
    parser.add_argument('--no-progress-bar', action='store_true', 
                        help='show progress bar')
    parser.add_argument('files', metavar='FN', nargs='*',
                        help='filenames of twitter dialogs in json format')
    args = parser.parse_args()

    # prepare filenames
    target_files = set()
    if args.target:
        for ln in open(args.target, 'r').readlines():
            target_files.add(os.path.join(args.data_dir, ln.strip() + '.json'))
    for fn in args.files:
        target_files.add(fn)

    target_files = sorted(list(target_files))
    # read ID list
    id_list = json.load(open(args.id_list,'r'))
    id_pool = set()
    for di in id_list:
        for turn in di:
            id_pool |= set(turn['ids'])
    # extract necessary tweets
    if not args.no_progress_bar:
        target_files = tqdm(target_files)
    tweet_pool = {}
    for fn in target_files:
        dialog_set = json.load(open(fn,'r'))
        for tid_str in dialog_set:
            for tweet in dialog_set[tid_str]:
                tid = tweet['id']
                if tid in id_pool:
                    tweet_pool[tid] = tweet
    # write text to file
    if args.output:
        fo = open(args.output,'w')
    else:
        fo = sys.stdout
    if not args.no_progress_bar:
        tweet_id_list = tqdm(id_list)

    n_dialogs = 0
    n_turns = 0
    n_turns_in_list = 0
    for dialog in tweet_id_list:
        user_name = ''
        user_first_name = ''
        system_name = ''
        # print a dialog 
        missed = False
        for ti,turn in enumerate(dialog):
            speaker = turn['speaker']
            six.print_('%s:' % speaker, file=fo, end='')
            if sum([tid in tweet_pool for tid in turn['ids']]) < len(turn['ids']):
                six.print_(' __MISSING__', file=fo)
                missed = True

            elif len(turn['ids'])==0 and ti==len(dialog)-1:
                six.print_(' __UNDISCLOSED__', file=fo)
                n_turns += 1

            else:
                for tid in turn['ids']:
                    tweet = tweet_pool[tid]
                    screen_name = tweet['user']['screen_name']
                    name = tweet['user']['name']
                    text = tweet['text']
                    if speaker == 'S':
                        if not args.debug:
                            text = preprocess(text, user_name, speaker=speaker, first_name=user_first_name)
                        system_name = screen_name
                    else:
                        if not args.debug:
                            text = preprocess(text, system_name, speaker=speaker)
                        # set user's screen name and first name to replace the names
                        # to a common symbol (e.g. <USER>) in system utterances
                        user_name = screen_name
                        tokens = name.split()
                        if len(tokens) > 0 and len(tokens[0]) > 2:
                            m = re.match(r'([A-Za-z0-9]+)$', tokens[0])
                            if m:
                                user_first_name = m.group(1)

                    six.print_(' %s' % text, file=fo, end='')
                six.print_('', file=fo)
                n_turns += 1

        n_turns_in_list += len(dialog)
        if not missed:
            n_dialogs += 1
        six.print_('', file=fo)

    if args.output:
        fo.close()

    print('--------------------------------------------------------')
    print('Number of successfully extracted dialogs: %d in %d' % (n_dialogs, len(tweet_id_list)))
    print('Number of successfully extracted turns: %d in %d' % (n_turns, n_turns_in_list))
    print('--------------------------------------------------------')

