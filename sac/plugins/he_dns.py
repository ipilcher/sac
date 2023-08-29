# SPDX-License-Identifier:  GPL-3.0-or-later

#
#       SAC - Source Address Client
#
#       Hurricane Electric DNS plug-in
#
#       Copyright 2023 Ian Pilcher <arequipeno@gmail.com>
#


import logging
import random
import requests
import time

import dns.resolver
import sac.plugin


HE_DYNDNS_URL = 'https://dyn.dns.he.net/nic/update'

_LOG = logging.getLogger('sac')


class HEDNSPlugin(sac.plugin.Plugin):

    def __init__(self, name, cfg):
        super().__init__(name)
        self.username = cfg['username']
        self.password = cfg['password']
        self.hostname = cfg['hostname']
        self.ns_names = cfg['nameservers']
        self.random = random.Random(time.time() + hash(name))

    def init(self):
        nameservers = set()
        for ns in self.ns_names:
            try:
                answer = dns.resolver.resolve(ns, lifetime=2.0, search=False)
                for rr in answer:
                    nameservers.add(rr.address)
            except Exception as e:
                _LOG.warning(f'Failed to resolve {ns}: {e}')
        if not nameservers:
            raise sac.plugin.PluginException(
                    self, 'Failed to resolve any nameservers'
                )
        self.nameservers = list(nameservers)

    def check(self, ip_str):
        resolver = dns.resolver.Resolver()
        resolver.nameservers = list(self.nameservers)
        answer = resolver.resolve(self.hostname, search=False)
        return len(answer.rrset) == 1 and answer.rrset[0].address == ip_str

    def update(self, ip_str):
        auth = ( self.hostname, self.password )
        params = { 'hostname': self.hostname, 'myip': ip_str }
        response = requests.get(HE_DYNDNS_URL, auth=auth, params=params)
        result = (response.text.split() + [ None ])[0]
        if response.status_code != 200 or result not in { 'good', 'nochg' }:
            _LOG.err('Failed to update DNS: {}: {}'.format(
                    response.status_code, response.text
                ))
            return False
        _LOG.info(f'Set DNS record for {self.hostname} to {ip_str}')
        return True


# kate: indent-width 4; replace-tabs on;
