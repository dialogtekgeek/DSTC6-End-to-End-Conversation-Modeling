#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""search_twitter_accounts.py:
   A script to search twitter accounts with REST API 1.1.

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import argparse 
import json
import sys
import os
import logging
from requests_oauthlib import OAuth1Session
from twitter_api import GETUsersSearch

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

    # open a session 
    session = OAuth1Session(ConsumerKey, ConsumerSecret, AccessToken, AccessTokenSecret)

    # collect users from the queries
    user_search = GETUsersSearch(session)
    user_search.setParams(' '.join(args.queries), target_count=args.count)
    user_search.waitReady()
    result = user_search.call()
    logger.info('obtained %d users' % len(result))

    if args.dump:
        logger.info('writing raw data to file %s' % args.dump)
        json.dump(result, open(args.dump,'w'), indent=2)

    if args.output:
        logger.info('writing screen names to file %s' % args.output)
        with open(args.output,'w') as f:
            for user in result:
                f.write(user['screen_name'] + '\n')
    else:
        for user in result:
            sys.stdout.write(user['screen_name'] + '\n')


if __name__ =="__main__":
    # parse command line
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='config.ini', help="config file")
    parser.add_argument('-o', '--output', help="output screen names to a file")
    parser.add_argument('-D', '--dump', help="dump raw data to a file")
    parser.add_argument('-l', '--logfile', help="set a log file")
    parser.add_argument('-n', '--count', default=100, type=int, 
                        help="maximum number of tweets acquired from each account")
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('queries', metavar='KW', nargs='+', help='query keywords')
    args = parser.parse_args()

    # set up the logger
    stdhandler = logging.StreamHandler()
    stdhandler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(stdhandler)
    if args.logfile:
        filehandler = logging.FileHandler(args.logfile, mode='w')
        filehandler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(filehandler)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    logger.info('started to collect twitter accounts')
    logger.debug('args=' + str(args))

    # call main process
    try:
        Main(args)
    except:
        logger.exception('exited with an error')
        sys.exit(1)

    logger.info('done')

