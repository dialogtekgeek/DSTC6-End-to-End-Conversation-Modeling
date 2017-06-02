#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""collect_twitter_dialogs.py:
   A script to acquire twitter dialogs with REST API 1.1.

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import argparse 
import json
import sys
import six
import os
import re
import time
import logging
from requests_oauthlib import OAuth1Session
from twitter_api import GETStatusesUserTimeline
from twitter_api import GETStatusesLookup

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser

# create logger object
logger = logging.getLogger("root")
logger.setLevel(logging.INFO)

def Main(args):
    # get access keys from a config file
    config = ConfigParser()
    config.read(args.config)
    ConsumerKey = config.get('AccessKeys','ConsumerKey')
    ConsumerSecret = config.get('AccessKeys','ConsumerSecret')
    AccessToken = config.get('AccessKeys','AccessToken')
    AccessTokenSecret = config.get('AccessKeys','AccessTokenSecret')

    # obtain targets
    targets = args.names
    if args.target:
        for line in open(args.target,'r').readlines():
            name = line.strip()
            if not name.startswith('#'):
                targets.append(name)

    # make a directory to store acquired dialogs
    if args.outdir:
        if not os.path.exists(args.outdir):
            os.mkdir(args.outdir)

    # open a session 
    session = OAuth1Session(ConsumerKey, ConsumerSecret, AccessToken, AccessTokenSecret)

    # setup API object
    get_user_timeline = GETStatusesUserTimeline(session)
    get_user_timeline.setParams(target_count=args.count, reply_only=True)
    get_lookup = GETStatusesLookup(session)

    # collect dialogs from each target
    num_dialogs = 0
    num_past_dialogs = 0

    for name in targets:
        logger.info('-----------------------------')
        outfile = name + '.json'
        if args.outdir:
            outfile = os.path.join(args.outdir, outfile)

        ## collect tweets from an account
        logger.info('collecting tweets from ' + name)
        if os.path.exists(outfile):
            logger.info('restoring acquired tweets from ' + outfile)
            dialog_set = json.load(open(outfile,'r'))
            since_id = max([int(s) for s in dialog_set.keys()])
            num_past_dialogs += len(dialog_set)
        else:
            since_id = None
            dialog_set = {}

        get_user_timeline.setParams(name, max_id=None, since_id=since_id)
        get_user_timeline.waitReady()
        timeline_tweets = get_user_timeline.call()
        if timeline_tweets is None:
            logger.warn('skip %s with an error' % name)
            num_dialogs += len(dialog_set)
            continue

        logger.info('obtained %d new tweet(s)' % len(timeline_tweets))
        if len(timeline_tweets) == 0:
            logger.info('no dialogs have been added to ' + outfile)
            num_dialogs += len(dialog_set)
            continue

        ## collect source tweets
        logger.info("collecting source tweets in reply recursively")
        tweet_set = {}
        ## to avoid getting same tweets again, add tweets we aready have
        for tid,dialog in dialog_set.items():
            for tweet in dialog:
                tweet_set[tweet['id']] = tweet
        ## add new tweets and collect reply-ids as necessary
        source_ids = set()
        for tweet in timeline_tweets:
            tweet_set[tweet['id']] = tweet
            reply_id = tweet['in_reply_to_status_id']
            if reply_id is not None and reply_id not in tweet_set:
                source_ids.add(reply_id)
        ## acquire source tweets
        get_lookup.waitReady()
        while len(source_ids) > 0:
            get_lookup.setParams(source_ids)
            result = get_lookup.call()
            logger.info('obtained %d/%d tweets' % (len(result),len(source_ids)))
            new_source_ids = set()
            for tweet in result:
                tweet_set[tweet['id']] = tweet
                reply_id = tweet['in_reply_to_status_id']
                if reply_id is not None and reply_id not in tweet_set:
                    new_source_ids.add(reply_id)
            source_ids = new_source_ids

        ## reconstruct dialogs
        logger.info("restructuring the collected tweets as a set of dialogs")
        visited = set()
        new_dialogs = 0
        for tweet in timeline_tweets:
            tid = tweet['id']
            if tid not in visited: # ignore visited node (it's not a terminal)
                visited.add(tid)
                # backtrack source tweets and make a dialog
                dialog = [tweet]
                reply_id = tweet_set[tid]['in_reply_to_status_id']
                while reply_id is not None:
                    visited.add(reply_id)
                    # if there already exists a dialog associated with reply_id, 
                    # the dialog is deleted because it's not a complete dialog.
                    if str(reply_id) in dialog_set:
                        del dialog_set[str(reply_id)]
                    # insert a source tweet to the dialog
                    if reply_id in tweet_set:
                        dialog.insert(0,tweet_set[reply_id])
                    else:
                        break
                    # move to the previous tweet
                    reply_id = tweet_set[reply_id]['in_reply_to_status_id']

                # add the dialog only if it contains two or more turns,
                # where it is associated with its terminal tweet id.
                if len(dialog) > 1:
                    dialog_set[str(tid)] = dialog
                    new_dialogs += 1

        logger.info('obtained %d new dialogs' % new_dialogs)
        if new_dialogs > 0:
            logger.info('writing to file %s' % outfile)
            json.dump(dialog_set, open(outfile,'w'), indent=2)
        else:
            logger.info('no dialogs have been added to ' + outfile)

        num_dialogs += len(dialog_set)

    logger.info('-----------------------------')
    logger.info('obtained %d new dialogs' % (num_dialogs - num_past_dialogs))
    logger.info('now you have %d dialogs in total' % num_dialogs)


if __name__ =="__main__":
    # parse command line
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='config.ini', help="config file")
    parser.add_argument('-t', '--target', help="read account names from a file")
    parser.add_argument('-o', '--outdir', help="output directory")
    parser.add_argument('-l', '--logfile', help="set a log file")
    parser.add_argument('-n', '--count', default=-1, type=int, 
                        help="maximum number of tweets acquired from each account")
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('-s', '--silent', action='store_true', help="silent mode")
    parser.add_argument('names', metavar='NAME', nargs='*', help='account names')
    args = parser.parse_args()

    # set up the logger
    stdhandler = logging.StreamHandler()
    stdhandler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    if args.silent:
        stdhandler.setLevel(logging.WARN)
    logger.addHandler(stdhandler)

    if args.logfile:
        filehandler = logging.FileHandler(args.logfile, mode='w')
        filehandler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(filehandler)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    logger.info('started to collect twitter dialogs')
    logger.debug('args=' + str(args))

    # call main process
    try:
        Main(args)
    except:
        logger.exception('exited with an error')
        sys.exit(1)

    logger.info('done')

