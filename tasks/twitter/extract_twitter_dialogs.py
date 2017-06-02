#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""extract_twitter_dialogs.py:
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


def find_sequential_tweets(tweet, group):
    """ Check if the tweet is in multiple tweets of a single turn
        Args: 
           tweet: the target tweet
           group: list of groups of multiple tweets
        Return:
           index of group in which the target is included
           if no group found, return -1
    """
    if len(group) == 0:
        return -1
    tfm = '%a %b %d %H:%M:%S +0000 %Y'
    tw_time = datetime.strptime(tweet['created_at'], tfm)
    #print (time1)
    for m,elm in enumerate(group):
        for et in elm[1].values():
            #print(et['created_at'])
            tdiff = (tw_time - datetime.strptime(et['created_at'], tfm))
            if tweet['in_reply_to_status_id'] is not None \
               and tweet['in_reply_to_status_id']==et['in_reply_to_status_id'] \
               and tweet['user']['id']==et['user']['id'] \
               and abs(tdiff.total_seconds()) < 600:
                return m
    return -1


def validate_dialog(dialog, max_turns):
    """ Check if the dialog consists of multiple turns with equal or 
        less than max_turns by two users without truncated tweets.
        Args:
            dialog: target dialog
            max_turns: upper bound of #turns per dialog
        Return:
            True if the conditions are all satisfied
            False, otherwise
    """
    if len(dialog) > max_turns:
        return False
    # skip dialogs including truncated tweets or more users
    users = set()
    for utterance in dialog:
        for tid,tweet in utterance.items():
            if tweet['truncated'] == True:
                return False
            users.add(tweet['user']['id'])
    if len(users) != 2:
        return False
    return True


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


def print_dialog(dialog, fo, sys_name='', debug=False):
    """ print a dialog 
    args:
        dialog (list): list of tweet groups
        sys_name (str): screen_name of system
        file (object): file object to write text
        debug (bool): debug mode
    """
    user_name = ''
    user_first_name = ''
    prev_speaker = ''
    # print a dialog 
    for utterance in dialog:
        for n,tweet in enumerate(sorted(utterance.values(), key=lambda u:u['id'])):
            screen_name = tweet['user']['screen_name']
            name = tweet['user']['name']
            text = tweet['text']
            if debug:
                six.print_('### %s: %s' % (name,text), file=fo)

            if screen_name.lower() == sys_name.lower():
                speaker = 'S'
                text = preprocess(text, user_name, speaker=speaker, first_name=user_first_name)
            else:
                speaker = 'U'
                text = preprocess(text, system_name, speaker=speaker)
                # set user's screen name and first name to replace the names
                # to a common symbol (e.g. <USER>) in system utterances
                user_name = screen_name
                tokens = name.split()
                if len(tokens) > 0 and len(tokens[0]) > 2:
                    m = re.match(r'([A-Za-z0-9]+)$', tokens[0])
                    if m:
                        user_first_name = m.group(1)
                        #print tokens[0],user_first_name

            if prev_speaker:
                if prev_speaker != speaker:
                    six.print_('\n%s: %s' % (speaker,text), file=fo, end='')
                else: # connect to the previous tweet
                    six.print_(' %s' % (text), file=fo, end='')
            else:
                six.print_('%s: %s' % (speaker,text), file=fo, end='')

            prev_speaker = speaker

    six.print_('\n', file=fo)


if __name__ == "__main__":
    # parse command line
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target', help='read screen names from a file')
    parser.add_argument('-o', '--output', help='output processed text into a file')
    parser.add_argument('-d', '--debug', action='store_true', help='debug mode')
    parser.add_argument('--data-dir', help='specify data directory')
    parser.add_argument('--max-turns', default=20, 
                        help='exclude long dialogs by this number')
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
    # open output file
    if args.output:
        fo = open(args.output,'w')
    else:
        fo = sys.stdout

    # extract dialogs
    # (1) merge sparated tweets that can be considered one utterance
    # (2) filter irregular dialogs, e.g. too long, including truncated tweets, etc.
    # (3) tokenize and normalize sentence text
    if not args.no_progress_bar:
        target_files = tqdm(target_files)

    for fn in target_files:
        dialog_set = json.load(open(fn,'r'))
        m = re.search(r'(^|\/)([^\/]+)\.json',fn)
        if m:
            system_name = m.group(2)
        else:
            raise Exception('no match to a screen name in %s' % fn)

        # make a tweet tree to merge sequential tweets by the same user
        root = {}
        for tid_str in sorted(dialog_set.keys()):
            dialog = dialog_set[tid_str]
            if dialog[0]['lang'] == 'en':
                tid = dialog[0]['id']
                if tid not in root:
                    root[tid] = ([],{tid:dialog[0]})
                node = root[tid][0]
                for tweet in dialog[1:]:
                    tid = tweet['id']
                    m = find_sequential_tweets(tweet,node)
                    if m >= 0:
                        node[m][1][tid] = tweet
                    else:
                        node.append(([],{tid:tweet}))
                    node = node[m][0]
    
        # depth-first search and extract dialogs
        stack = []
        for tid in sorted(root.keys()):
            stack.append((root[tid][0], [root[tid][1]]))

        while len(stack)>0:
            node,dseq = stack.pop()
            if len(node) == 0:
                if validate_dialog(dseq, args.max_turns):
                    print_dialog(dseq, fo, sys_name=system_name, debug=args.debug)
            else:
                for elm in node:
                    stack.append((elm[0], dseq + [elm[1]]))

    if args.output:
        fo.close()

