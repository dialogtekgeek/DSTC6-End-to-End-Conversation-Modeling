#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""view twitter dialogs.

   Copyright (c) 2017 Takaaki Hori  (thori@merl.com)

   This software is released under the MIT License.
   http://opensource.org/licenses/mit-license.php

"""

import json
import sys
import six

if six.PY2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

if len(sys.argv) < 2:
    print ('usage: view_dialogs.py dialogs.json ...')
    sys.exit(1)

for fn in sys.argv[1:]:
    dialog_set = json.load(open(fn,'r'))
    for tid in sorted([int(s) for s in dialog_set.keys()]):
        dialog = dialog_set[str(tid)]
        lang = dialog[0]['lang']
        if lang == 'en':
            print ('--- ID:%d (length=%d) ---\n' % (tid, len(dialog)))
            for utterance in dialog:
                screen_name = utterance['user']['screen_name']
                name = utterance['user']['name']
                text = utterance['text']
                print ('%s (%s)' % (utterance['created_at'],utterance['id']))
                print ('%s (@%s) : %s\n' % (name, screen_name, text))

