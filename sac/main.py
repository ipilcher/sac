# SPDX-License-Identifier:  GPL-3.0-or-later

#
#       SAC - Source Address Client
#
#       Main loop
#
#       Copyright 2023 Ian Pilcher <arequipeno@gmail.com>
#

import ctypes
import logging
import os
import signal
import socket
import sys
import tomllib

from . import argp
from . import mcast
from . import plugin


_LOG = logging.getLogger(__name__)


class ExitSignal(Exception):
    pass


def _init_logger(args):
    if args.debug is not None:
        level = logging.DEBUG
        locn = '{filename}:{lineno}: '
    else:
        level = logging.INFO
        locn = ''
    if (use_syslog := args.syslog) is None:
        use_syslog = not sys.stderr.isatty()
    if use_syslog:
        hndlr = logging.handlers.SysLogHandler(address='/dev/log')
        fmt = f'{locn}{{levelname}}: {{message}}'
    else:
        hndlr = logging.StreamHandler()
        fmt = f'{{asctime}}: {locn}{{levelname}}: {{message}}'
    hndlr.setLevel(level)
    hndlr.setFormatter(logging.Formatter(fmt, style='{'))
    # Configure parent logger, so settings apply to all modules
    parent_logger = logging.getLogger(__name__.rsplit('.', 1)[0])
    parent_logger.setLevel(level)
    parent_logger.addHandler(hndlr)


def _signal_hndlr(signum, frame):
    _LOG.info(f'Received {signal.Signals(signum).name}; exiting')
    raise ExitSignal()


def _main():
    args = argp.parse()
    _init_logger(args)
    signal.signal(signal.SIGINT, _signal_hndlr)
    signal.signal(signal.SIGTERM, _signal_hndlr)
    with open(args.config, 'rb') as cf:
        cfg = tomllib.load(cf)
    _LOG.debug(f'Loaded configuration file: {args.config}')
    plugin.load(cfg)
    plugin.init()
    mcast.init(cfg, args.insecure)
    defsrc = '0.0.0.0'  # sent by sad when no default route exists
    while True:
        if (newsrc := mcast.recv()) is None:
            continue
        if newsrc == defsrc:
            _LOG.debug(f'Default source address ({defsrc}) has not changed')
            continue
        _LOG.info(f'Default source address changed from {defsrc} to {newsrc}')
        plugin.process(newsrc)
        defsrc = newsrc
        if args.one_shot:
            _LOG.info('One-shot mode selected; exiting')
            break


def main():
    try:
        _main()
    except ExitSignal:
        pass


# kate: indent-width 4; replace-tabs on;
