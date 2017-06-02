#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""python class to acquire twitter data with REST API 1.1.

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
from datetime import datetime

# get a logger object
logger = logging.getLogger('root')

# base API caller 
class TwitterAPI(object):
    def __init__(self, command, session):
        self.rest_api_url = 'https://api.twitter.com/1.1'
        self.error_code_url = 'https://dev.twitter.com/overview/api/response-codes'
        self.check_rate_limits = '/application/rate_limit_status'
        self.command = command
        self.session = session
        self.params = {}

    def call(self, retry=5):
        '''
        acquire data by a given method
        '''
        if len(self.params) == 0:
            raise Exception('parameters are not set for %s' % self.command)

        url = self.rest_api_url + self.command + '.json'
        n_errors = 0
        self.result = []
        while True:
            logger.debug('URL: ' + url)
            logger.debug('params: ' + str(self.params))
            res = self.session.get(url, params = self.params)
            if res.status_code == 200: # Success
                data = json.loads(res.text)
                if len(data) == 0:
                    break
                if self.extract(data) == False: # if no more data need to be acquired
                    break
                n_errors = 0
    
                # check if header includes 'X-Rate-Limit-Remaining'
                if 'X-Rate-Limit-Remaining' in res.headers \
                and 'X-Rate-Limit-Reset' in res.headers:
                    if int(res.headers['X-Rate-Limit-Remaining']) == 0:
                        waittime = int(res.headers['X-Rate-Limit-Reset']) \
                                    - time.mktime(datetime.now().timetuple())
                        logger.info('reached the rate limit ... wait %d seconds', waittime + 5)
                        time.sleep(waittime + 5)
                        self.waitReady(self.session)
                else:
                    self.waitReady(self.session)
    
            elif res.status_code==401 or res.status_code==404:
                logger.warn('Twitter API error %d, see %s' % (res.status_code, self.error_code_url))
                logger.warn('error occurred in %s' % self.command)
                return None
            else:
                n_errors += 1
                if n_errors > retry:
                    raise Exception('Twitter API error %d, see %s' % (res.status_code, self.error_code_url))
    
                logger.warn('Twitter API error %d, see %s' % (res.status_code, self.error_code_url))
                logger.warn('Service Unavailable ... wait 15 minutes')
                time.sleep(905)
    
        return self.result 

    # parameter setting
    def _set_param(self, key, value, default=None):
        if value is None: # if value is None, the parameter is removed
            if key in self.params:
                del self.params[key]
        elif default is None or value != default: # if not default, set the parameter
            self.params[key] = value


    def getWaitTime(self, res_text):
        waittime = 0
        for command in [self.command, self.check_rate_limits]:
            category = re.sub(r'^/([^\s\/]+)/.*$', '\\1', command)
            remaining = int(res_text['resources'][category][command]['remaining'])
            reset = int(res_text['resources'][category][command]['reset'])
            if remaining == 0:
                waittime = max(waittime, reset - time.mktime(datetime.now().timetuple()))

        return waittime


    def waitReady(self, retry=5):
        '''
        check status, and wait until it gets available
        '''
        n_errors = 0
        while True:
            res = self.session.get(self.rest_api_url + self.check_rate_limits + '.json')
            if res.status_code == 200: # Success
                res_text = json.loads(res.text)
                waittime = self.getWaitTime(res_text)
                if (waittime > 0):
                    logger.info('reached the rate limit ... wait %d seconds' % (waittime+5))
                    time.sleep(waittime+5)
                    n_errors = 0
                else:
                    break
    
            else:
                n_errors += 1
                if n_errors > retry:
                    raise Exception('Twitter API error %d, see %s' % (res.status_code, self.error_code_url))
    
                logger.warn('Twitter API error %d, see %s' % (res.status_code, self.error_code_url))
                logger.warn('Service Unavailable ... wait 15 minutes')
                time.sleep(905)

    
## some methods to get data

class GETSearchTweets(TwitterAPI):
    '''
      Object to acquire tweets by a query
      see https://dev.twitter.com/rest/reference/get/search/tweets
      Limit: Requests / 15-min window (app auth) <= 450
    '''
    def __init__(self, session):
        super(GETSearchTweets, self).__init__('/search/tweets', session)
        self.query = {}
        self.target_count = -1  # default: unlimited
        self.reply_only = False

    def setParams(self, query='', target_count=-1, since_id=0, max_id=0,
                  reply_only=None):
        self._set_param('q', query, '')
        self._set_param('since_id', since_id, 0)
        self._set_param('max_id', max_id, 0)
        if target_count > 0:
            self._set_param('count', min(target_count,100))
            self.target_count = target_count
        else:
            self._set_param('count', 100)

        if reply_only is not None:
            self.reply_only = reply_only

    def extract(self, tweets):
        logger.debug('search_metadata:' + str(tweets['search_metadata']))
        for tweet in tweets['statuses']:
            # extract reply tweets only
            if self.reply_only and tweet['in_reply_to_status_id'] is None:
                continue
            # extract entries
            self.result.append(tweet)
            if len(self.result) % 100 == 0:
                logger.info('...acquired %d tweets ' % len(self.result))
            if self.target_count > 0 and len(self.result) >= self.target_count:
                return False

        # for the next call
        if len(tweets['statuses']) > 0:
            self._set_param('max_id', tweets['statuses'][-1]['id'] - 1) # update max_id
            return True
        else:
            return False


class GETStatusesUserTimeline(TwitterAPI):
    '''
      Object to acquire tweets along a user time line
      see https://dev.twitter.com/rest/reference/get/statuses/user_timeline
      Limit: Requests / 15-min window (app auth) <= 1500
    '''
    def __init__(self, session):
        super(GETStatusesUserTimeline, self).__init__('/statuses/user_timeline', session)
        self.params['include_rts'] = 'false'
        self.params['exclude_replies'] = 'false'
        self.target_count = 0
        self.reply_only = False

    def setParams(self, name='', target_count=0, since_id=0, max_id=0,
                 reply_only=None):
        self._set_param('screen_name', name, '')
        self._set_param('since_id', since_id, 0)
        self._set_param('max_id', max_id, 0)
        if target_count > 0:
            self._set_param('count', min(target_count,100))
            self.target_count = target_count
        else:
            self._set_param('count', 100)

        if reply_only is not None:
            self.reply_only = reply_only

    def extract(self, tweets):
        for tweet in tweets:
            # extract reply tweets only
            if self.reply_only and tweet['in_reply_to_status_id'] is None:
                continue
            # store tweets
            self.result.append(tweet)
            if len(self.result) % 100 == 0:
                logger.info('...acquired %d tweets ' % len(self.result))
            if self.target_count>0 and len(self.result) >= self.target_count:
                return False

        # for the next call
        if len(tweets) > 0:
            self._set_param('max_id', tweets[-1]['id'] - 1) # update max_id
            return True
        else:
            return False


class GETStatusesLookup(TwitterAPI):
    '''
      Object to acquire tweets by ID numbers
      see https://dev.twitter.com/rest/reference/get/statuses/lookup
      Limit: Requests / 15-min window (app auth) <= 300
    '''
    def __init__(self, session):
        super(GETStatusesLookup, self).__init__('/statuses/lookup', session)
        self.count = 100 # cat get up to 100 tweets at once

    def setParams(self, id_set=None):
        if id_set is not None:
            self.id_list = list(id_set)
            self.params['id'] = ','.join([str(n) for n in self.id_list[0:self.count]])
        self.total_count = 0

    def extract(self, tweets):
        for tweet in tweets:
            self.result.append(tweet)
            if len(self.result) % 100 == 0:
                logger.info('...acquired %d tweets ' % len(self.result))

        self.total_count += self.count
        if self.total_count >= len(self.id_list):
            return False

        # for the next call
        sub_ids = self.id_list[self.total_count:self.total_count+self.count]
        self.params['id'] = ','.join([str(n) for n in sub_ids])
        return True


class GETUsersSearch(TwitterAPI):
    '''
      Object to search users by a query
      see https://dev.twitter.com/rest/reference/get/users/search
      Limit: Requests / 15-min window (user auth) <= 900
    '''
    def __init__(self, session):
        super(GETUsersSearch, self).__init__('/users/search', session)
        self.target_count = 100 # default
        self.params['count'] = 20 # can get 20 entries per page

    def setParams(self, query='', target_count=0):
        self._set_param('q', query, '')
        if target_count > 0:
            self.target_count = target_count
        self.params['page'] = 1

    def extract(self, text):
        for user in text:
            self.result.append(user)
            if len(self.result) % 100 == 0:
                logger.info('...acquired %d users ' % len(self.result))
            if len(self.result) >= self.target_count:
                return False

        # for the next call
        self.params['page'] += 1
        return True

