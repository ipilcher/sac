# SPDX-License-Identifier:  GPL-3.0-or-later

#
#       SAC - Source Address Client
#
#       Command line argument parsing
#
#       Copyright 2023 Ian Pilcher <arequipeno@gmail.com>
#


import argparse


class _GenericStoreOnceAction(argparse.Action):

    def __init__(self, option_strings, dest, nargs, const=None, default=None,
                 help=None):
        assert (const is None) == (nargs != 0)
        self.set = False
        super().__init__(option_strings, dest, nargs=nargs, const=const,
                         default=default, help=help)

    def __call__(self, parser, namespace, values, option_string):
        if self.set:
            parser.error(f'Duplicate option: {"/".join(self.option_strings)}')
        self.set = True
        setattr(namespace, self.dest, values)


class _StoreOnceAction(_GenericStoreOnceAction):

    def __init__(self, option_strings, dest, default=None, help=None):
        super().__init__(option_strings, dest, 1, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string):
        super().__call__(parser, namespace, values[0], option_string)


class _StoreConstOnceAction(_GenericStoreOnceAction):

    def __init__(self, option_strings, dest, const, help=None):
        super().__init__(option_strings, dest, 0, const=const, help=help)

    def __call__(self, parser, namespace, values, option_string):
        super().__call__(parser, namespace, self.const, option_string)


class _SetTrueAction(_StoreConstOnceAction):

    def __init__(self, option_strings, dest, help=None):
        super().__init__(option_strings=option_strings, dest=dest, const=True,
                         help=help)


class _SetFalseAction(_StoreConstOnceAction):

    def __init__(self, option_strings, dest, help=None):
        super().__init__(option_strings=option_strings, dest=dest, const=False,
                         help=help)


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action=_SetTrueAction,
                        help='Enable logging of DEBUG messages')
    parser.add_argument('-I', '--insecure', action=_SetTrueAction,
                        help='Process announcements from any source')
    parser.add_argument('-O', '--one-shot', action=_SetTrueAction,
                        help='Quit after first source address change')
    parser.add_argument('-c', '--config', action=_StoreOnceAction,
                        default='/etc/sac/sac.conf',
                        help='Specify configuration file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-e', '--stderr', action=_SetFalseAction, dest='syslog',
                    help='Log messages to stderr (not syslog)')
    group.add_argument('-l', '--syslog', action=_SetTrueAction,
                    help='Log messages to syslog (not stderr)')
    args = parser.parse_args()

    return args

# kate: indent-width 4; replace-tabs on;
