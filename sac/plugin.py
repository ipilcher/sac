# SPDX-License-Identifier:  GPL-3.0-or-later

#
#       SAC - Source Address Client
#
#	Plugin stuff
#
#       Copyright 2023 Ian Pilcher <arequipeno@gmail.com>
#


import abc
import importlib
import os.path
import logging
import sys

from . import util


_LOG = logging.getLogger(__name__)


class PluginException(Exception):

    def __init__(self, plugin, msg):
        super().__init__(f'{plugin.name}: {msg}')
        self.plugin = plugin
        plugin.disabled = True


class Plugin(abc.ABC):

    __classes = {}
    __plugins = []

    def __init_subclass__(cls):
        Plugin.__classes[f'{cls.__module__}.{cls.__qualname__}'] = cls

    @staticmethod
    def __load_plugin_file(fpath):
        mod_name, _ = os.path.splitext(os.path.basename(fpath))
        mod_name = '_sac_file_plugins_.' + mod_name
        spec = importlib.util.spec_from_file_location(mod_name, fpath)
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)

    @classmethod
    def _load(cls, cfg):
        for m in util.get_nested(cfg, 'plugins', 'modules', default=[]):
            importlib.import_module(m)
        for f in util.get_nested(cfg, 'plugins', 'files', default=[]):
            cls.__load_plugin_file(f)
        for pname, pcfg in cfg.get('plugin', {}).items():
            if (clsname := pcfg.get('class')) is None:
                raise Exception(f'Plugin class not specified: {pname}')
            if (pcls := cls.__classes.get(clsname)) is None:
                raise Exception(f'Plugin class not found: {clsname}')
            cls.__plugins.append(pcls(pname, pcfg))
            _LOG.info(f'Loaded plugin: {pname}')
        if not cls.__plugins:
            _LOG.warning("No plugins configured; won't do anything")

    @classmethod
    def _init(cls):
        for p in cls.__plugins:
            try:
                p.init()
            except PluginException as e:
                _LOG.error(e)
                _LOG.notice(f'Disabling plugin: {e.plugin.name}')
                p.disabled = True

    def __init__(self, name, cfg=None):
        self.name = name
        self.disabled = False

    @classmethod
    def _process(cls, newsrc):
        for p in cls.__plugins:
            if p.disabled:
                _LOG.debug(f'Skipping disabled plugin: {p.name}')
                continue
            try:
                if p.check(newsrc):
                    _LOG.info(f'{p.name}: already using new source address')
                    continue
                _LOG.info(f'{p.name}: not using new source address; updating')
                p.update(newsrc)
                _LOG.info(f'{p.name}: updated with new source address')
            except PluginException as e:
                _LOG.error(e)
                _LOG.notice(f'Disabling plugin: {e.plugin.name}')
                p.disabled = True

    def init(self):
        pass

    @abc.abstractmethod
    def check(self, ip_str):
        pass

    @abc.abstractmethod
    def update(self, ip_str):
        pass

    def cleanup(self):
        pass


def load(cfg):
    Plugin._load(cfg)

def init():
    Plugin._init()

def process(newsrc):
    Plugin._process(newsrc)


# kate: indent-width 4; replace-tabs on;
