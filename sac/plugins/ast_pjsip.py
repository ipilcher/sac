# SPDX-License-Identifier:  GPL-3.0-or-later

#
#       SAC - Source Address Client
#
#       Asterisk PJSIP plug-in
#
#       Copyright 2023 Ian Pilcher <arequipeno@gmail.com>
#


import errno
import logging
import mmap
import os
import pathlib
import re

import sac.plugin


_DEFAULT_CONF_FILE = '/etc/asterisk/pjsip.conf'
_DEFAULT_STATE_DIR = '/run/sac_ast_pjsip'
_DEFAULT_FLAG_FILE = 'pjsip_reload_needed'


class ConfPattern(object):
    """re.Pattern wrapper that has a pjsip.conf key name attribute."""

    def __init__(self, key, pattern, flags):
        self.key = key
        self.pattern = re.compile(pattern, flags)


_MEDIA_ADDR_PATTERN = ConfPattern(
        'external_media_address',
        rb'^external_media_address = ('
                rb'[12]?[0-9]?[0-9]'
                rb'\.'
                rb'[12]?[0-9]?[0-9]'
                rb'\.[12]?[0-9]?[0-9]'
                rb'\.'
                rb'[12]?[0-9]?[0-9]'
            rb')$',
        flags=re.MULTILINE
    )

_SIGNALING_ADDR_PATTERN = ConfPattern(
        'external_signaling_address',
        rb'external_signaling_address = ('
                rb'[12]?[0-9]?[0-9]'
                rb'\.'
                rb'[12]?[0-9]?[0-9]'
                rb'\.[12]?[0-9]?[0-9]'
                rb'\.'
                rb'[12]?[0-9]?[0-9]'
            rb')$',
        flags=re.MULTILINE
    )

_SUBST_PATTERN = re.compile(
        rb'(external_(?:(?:media)|(?:signaling))_address = )'
                rb'[12]?[0-9]?[0-9]'
                rb'\.'
                rb'[12]?[0-9]?[0-9]'
                rb'\.[12]?[0-9]?[0-9]'
                rb'\.'
                rb'[12]?[0-9]?[0-9]'
            rb'$',
        flags=re.MULTILINE
    )

_LOG = logging.getLogger('sac')


class AsteriskPJSIPPlugin(sac.plugin.Plugin):

    def __init__(self, name, cfg):
        super().__init__(name)
        self.conf_file = cfg.get('conf_file', _DEFAULT_CONF_FILE)
        cfbase = os.path.basename(self.conf_file)
        state_dir = cfg.get('state_dir', _DEFAULT_STATE_DIR)
        self.new_conf_file = cfg.get('new_conf_file', f'{state_dir}/{cfbase}')
        self.flag_file = cfg.get(
                'reload_flag_file', f'{state_dir}/{_DEFAULT_FLAG_FILE}'
            )
        _LOG.debug(f'{self.name}: conf_file: {self.conf_file}')
        _LOG.debug(f'{self.name}: new_conf_file: {self.new_conf_file}')
        _LOG.debug(f'{self.name}: reload_flag_file: {self.flag_file}')

    def _get_addr(self, cp, buf):
        i = cp.pattern.finditer(buf)
        if (match := next(i, None)) is None:
            raise sac.plugin.PluginException(
                    self, f'{cp.key} not found in {self.conf_file}'
                )
        if next(i, None) is not None:
            raise sac.plugin.PluginException(
                    self, f'{cp.key} found more than once in {self.conf_file}'
                )
        return match.group(1)

    def check(self, ip_str):
        ipb = ip_str.encode('ascii')
        with (open(self.conf_file, 'rb') as f,
                mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m):
            media_addr = self._get_addr(_MEDIA_ADDR_PATTERN, m)
            signaling_addr = self._get_addr(_SIGNALING_ADDR_PATTERN, m)
            return media_addr == ipb and signaling_addr == ipb

    def _write_new_conf(self, new):
        try:
            os.remove(self.new_conf_file)
        except EnvironmentError as e:
            if e.errno != errno.ENOENT:
                raise
        with open(self.new_conf_file, 'wb') as f:
            f.write(new)
        pathlib.Path(self.flag_file).touch(exist_ok=True)

    def update(self, ip_str):
        with open(self.conf_file, 'rb') as f:
            old = f.read()
        # Check that the existing file is what we expect
        self._get_addr(_MEDIA_ADDR_PATTERN, old)
        self._get_addr(_SIGNALING_ADDR_PATTERN, old)
        ipb = ip_str.encode('ascii')
        new = _SUBST_PATTERN.sub(lambda match: match.group(1) + ipb, old)
        self._write_new_conf(new)


# kate: indent-width 4; replace-tabs on;
