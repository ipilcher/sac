# SPDX-License-Identifier:  GPL-3.0-or-later

#
#       SAC - Source Address Client
#
#	Package initialization
#
#       Copyright 2023 Ian Pilcher <arequipeno@gmail.com>
#


import logging
import sys


class _SACLogger(logging.getLoggerClass()):
    """A Logger that supports NOTICE and FATAL levels."""

    NOTICE = (logging.INFO + logging.WARNING) // 2
    FATAL = logging.CRITICAL

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        logging.addLevelName(type(self).FATAL, 'FATAL')
        logging.addLevelName(type(self).NOTICE, 'NOTICE')

    def notice(self, msg, *args, **kwargs):
        self._log(type(self).NOTICE, msg, args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        self._log(type(self).FATAL, msg, args, **kwargs)
        sys.exit(1)


# Make it the default
logging.setLoggerClass(_SACLogger)


# kate: indent-width 4; replace-tabs on;
