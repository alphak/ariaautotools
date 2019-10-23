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
this tool used to automaticly selected files which needed to download.
files' extension in exts list will not be selected
files whose name contain the strings in namefilters will not be selected
'''

from __future__ import unicode_literals
import os, urllib2, json, argparse, logging, yaml
import logging.config
import codecs
# from datetime import datetime

#1024*1024=1048576
MEGABYTES = 1048576
FILESIZETHRESHOLD = 2000
FILELOWERBOUND = 50

parser = argparse.ArgumentParser(
    description=
    'automaticly select files to be downloaded in all bittorrent stoped/paused task'
)
parser.add_argument(
    '-t', '--token', type=str, default='your-token', help='rpc-token')
parser.add_argument(
    '-r',
    '--host',
    type=str,
    default='http://localhost:6800/jsonrpc',
    help='http://ip-or-domain-name:aria2c-port/jsonrpc]')
parser.add_argument(
    '-o',
    '--offset',
    type=int,
    default=1,
    help=
    'offset is an integer specifying the offset from the least recently stopped download'
)
parser.add_argument(
    '-n',
    '--num',
    type=int,
    default=200,
    help=
    'num is an integer specifying the max number of downloads to be returned')
parser.add_argument(
    '-e',
    '--fexts',
    type=str,
    default='./fexts.lst',
    help='file extension filter conf path')
parser.add_argument(
    '-k',
    '--fkw',
    type=str,
    default='./fkw.lst',
    help='content key word filter conf path')
parser.add_argument(
    '-l',
    '--logconf',
    type=str,
    default='./logging.yaml',
    help='logging conf path')
args = parser.parse_args()


def setupAndGetLogger(default_path=args.logconf,
                      default_level=logging.DEBUG,
                      env_key="LOG_CFG",
                      loggername="arialogger"):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, "r") as f:
            config = yaml.load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

    logger = logging.getLogger(loggername)
    return logger


def readList(fname):
    varLst = []
    with codecs.open(fname, 'r', encoding='utf-8') as f:
        for line in f:
            varLst.append(line.replace('\n', ''))
    return varLst


def ariaRpcCall(jsonobj, host, logger):
    jsonreq = json.dumps(jsonobj)
    logger.debug("json request will be sent with [%s]" % jsonreq)
    response = urllib2.urlopen(host, jsonreq)
    retJson = json.load(response)
    logger.debug("json response recieved with [%s]" % retJson)
    return retJson


def hasFileEndsWith5AndSmallerSize(filesList, file_name):
    for oneFile in filesList:
        fPath = oneFile['path']
        fSize = oneFile['length']
        file_size = long(fSize) / MEGABYTES
        staPath = fPath.replace('//', '/')
        fbasename = os.path.basename(staPath)
        (fname, fext) = os.path.splitext(fbasename)
        if fname == file_name or fext.lower(
        ) != '.mp4' or file_size < FILELOWERBOUND:
            continue

        if fname.endswith('-5') and file_size < FILESIZETHRESHOLD:
            return True
    return False


def hasFileMoreLargerButLessThanThreshold(filesList, file_name, the_size):
    for oneFile in filesList:
        fPath = oneFile['path']
        fSize = oneFile['length']
        file_size = long(fSize) / MEGABYTES
        staPath = fPath.replace('//', '/')
        fbasename = os.path.basename(staPath)
        (fname, fext) = os.path.splitext(fbasename)
        if fname == file_name or fext.lower(
        ) != '.mp4' or file_size < FILELOWERBOUND or file_size > FILESIZETHRESHOLD:
            continue

        if file_size > the_size:
            return True
    return False


def doFilter(tellWaitingRespJson, exts, namefilters, args, logger):
    result = tellWaitingRespJson['result']
    for oneRes in result:
        filesList = oneRes['files']
        taskGid = oneRes['gid']
        selectedIndexs = []

        for oneFile in filesList:
            fIndex = oneFile['index']
            fSelected = oneFile['selected']
            fPath = oneFile['path']
            fSize = oneFile['length']
            # file extension check
            staPath = fPath.replace('//', '/')
            fbasename = os.path.basename(staPath)
            (fname, fext) = os.path.splitext(fbasename)
            logger.debug(
                "gid=[%s] index=[%s] selected=[%s] name=[%s], size=[%s]" %
                (taskGid, fIndex, fSelected, fbasename, fSize))
            willSelected = 'true'
            if fext.lower() in exts:
                willSelected = 'false'

            for ll in namefilters:
                logging.debug("current str to find in name=[%s]" % ll)
                if fname.find(ll) > -1:
                    willSelected = 'false'
                    break

            if willSelected == 'true' and fname.endswith('-5-5'):
                willSelected = 'false'

            if willSelected == 'true' and fSelected == 'true':
                selectedIndexs.append(fIndex)
                if (fext.lower() == '.mp4'):
                    file_size = long(fSize) / MEGABYTES
                    if not fname.endswith('-5'):
                        if file_size > FILESIZETHRESHOLD:
                            if hasFileEndsWith5AndSmallerSize(
                                    filesList, fname):
                                selectedIndexs.remove(fIndex)
                    else:
                        if hasFileMoreLargerButLessThanThreshold(
                                filesList, fname, file_size):
                            selectedIndexs.remove(fIndex)

        if len(selectedIndexs) > 0:
            selectIndexStr = ','.join(selectedIndexs)
            logger.info("task[gid=%s has file selection list=[%s]" %
                        (taskGid, selectIndexStr))

            chgRespJson = ariaRpcCall({
                'jsonrpc':
                '2.0',
                'id':
                'autoselepy',
                'method':
                'aria2.changeOption',
                'params': [
                    'token:%s' % args.token, taskGid,
                    {
                        'select-file': selectIndexStr
                    }
                ]
            }, args.host, logger)
            logger.info("%s" % chgRespJson)


def main():
    #init logger
    logger = setupAndGetLogger()
    logger.info(
        "parameters token=%s host=%s offset=%d num=%d fexts=%s fkw=%s logconf=%s"
        % (args.token, args.host, args.offset, args.num, args.fexts, args.fkw,
           args.logconf))
    #init filter's list value
    exts = readList(args.fexts)
    namefilters = readList(args.fkw)

    logger.debug("file extension filters list=%s" % (exts))
    logger.debug("file content filters list=%s" % (namefilters))

    #get waiting tasks from remote aria2 server through rpc call
    respJsonData = ariaRpcCall({
        'jsonrpc':
        '2.0',
        'id':
        'autoselepy',
        'method':
        'aria2.tellWaiting',
        'params':
        ['token:%s' % args.token, args.offset, args.num, ['gid', 'files']]
    }, args.host, logger)
    logger.debug("aria2.tellWaiting rpc response data=[%s]" % respJsonData)

    doFilter(respJsonData, exts, namefilters, args, logger)


if __name__ == '__main__':
    main()
