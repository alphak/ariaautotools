#!/usr/bin/python
# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) 2019 wedohz mail: mstrwd@163.com

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
dynamicly update aria2c goloble option:bt-tracker with trackers provided by
url refer:https://github.com/ngosang/trackerslist
'''

from __future__ import unicode_literals
import os, urllib2, logging, argparse, yaml
import logging.config
import codecs
from ariaautosele import setupAndGetLogger, ariaRpcCall

parser = argparse.ArgumentParser(
    description='automaticly select files to be downloaded in all bittorrent stoped/paused task'
)
parser.add_argument(
    '-t', '--token', type=str, default='aria1123Ak(:', help='rpc-token')
parser.add_argument(
    '-r',
    '--host',
    type=str,
    default='http://localhost:6800/jsonrpc',
    help='http://ip-or-domain-name:aria2c-port/jsonrpc]')
parser.add_argument(
    '-u',
    '--url',
    type=str,
    default='https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best_ip.txt',
    help='web file to retrieve bt trackers'
)
args = parser.parse_args()


def main():
    logger = setupAndGetLogger()
    logger.info('rpc-token=[%s], host=[%s], url[%s]' % (args.token, args.host, args.url))

    file_content = urllib2.urlopen(args.url).read()
    logger.info('web file content=[%s]' % file_content)

    trackerLst = file_content.split('\n\n')
    trackerStr = ','.join(trackerLst)[:-1]
    logger.info('the newly generated bt trackers=[%s]' % trackerStr)

    chgRespJson = ariaRpcCall({
                'jsonrpc':
                '2.0',
                'id':
                'autoselepy',
                'method':
                'aria2.changeGlobalOption',
                'params': [
                    'token:%s' % args.token,
                    {
                        'bt-tracker': trackerStr
                    }
                ]
            }, args.host, logger)
    logger.info("%s" % chgRespJson)


if __name__ == '__main__':
    main()