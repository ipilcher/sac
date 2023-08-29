# SPDX-License-Identifier:  GPL-3.0-or-later

#
#       SAC - Source Address Client
#
#	Multicast stuff
#
#       Copyright 2023 Ian Pilcher <arequipeno@gmail.com>
#


import ctypes
import logging
import socket

import pyroute2

from . import util


_DEF_LISTEN_PORT = 4242
_DEF_LISTEN_ADDR = '239.255.42.42'
_DEF_SOURCE_PORT = 42
_DEF_ROUTE_DEST = '8.8.8.8'

_LOG = logging.getLogger(__name__)


class _in_addr(ctypes.Structure):
    """Python representation of a ``struct in_addr``."""

    _fields_ = [
        ('s_addr', ctypes.c_uint32)
    ]

    @classmethod
    def from_bytes(cls, ip_bytes):
        return cls.from_buffer_copy(ip_bytes)

    @classmethod
    def from_str(cls, ip_str):
        return cls.from_bytes(socket.inet_aton(ip_str))


class _ip_mreqn(ctypes.Structure):
    """Python representation of a ``struct ip_mreqn``."""

    _fields_ = [
        ('imr_multiaddr', _in_addr),
        ('imr_address', _in_addr),
        ('imr_ifindex', ctypes.c_int)
    ]


_socket = None


def _get_rt(dest):
    """Get interface index and (possibly) gateway of route to a destination."""
    ipr = pyroute2.IPRoute()
    nlmsg = ipr.route('get', dst=dest)[0]
    ifindex = None
    gateway = None
    for a in nlmsg['attrs']:
        if a[0] == 'RTA_OIF':
            ifindex = int(a[1])
        if a[0] == 'RTA_GATEWAY':
            gateway = a[1]
    if ifindex is None:
        _LOG.fatal(f'Failed to get default source interface for {dest}')
    return ifindex, gateway


def _get_ifindex(gateway):
    """Get the interface index used to communicate with a known gateway."""
    ifindex, _ = _get_rt(gateway)
    return ifindex


def _get_defrt(dest):
    """Get the interface index and gateway of the route to a destination."""
    ifindex, gateway = _get_rt(dest)
    if gateway is None:
        _LOG.fatal(f'Failed to get default gateway for {dest}')
    return ifindex, gateway


def init(cfg, insecure):
    global _socket
    if (gateway := util.get_nested(cfg, 'route', 'gateway')) is None:
        # gateway not specified; detect default route
        rtdest = util.get_nested(
                cfg, 'route', 'destination', default=_DEF_ROUTE_DEST
            )
        ifindex, gateway = _get_defrt(rtdest)
    else:
        # gateway specified; determine source interface
        if (ifname := util.get_nested(cfg, 'listen', 'interface')) is None:
            ifindex = _get_ifindex(gateway)
        else:
            ifindex = socket.if_nametoindex(ifname)
    _socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        )
    mcast_addr = util.get_nested(
            cfg, 'listen', 'address', default=_DEF_LISTEN_ADDR
        )
    mcast_port = util.get_nested(
            cfg, 'listen', 'port', default=_DEF_LISTEN_PORT
        )
    _socket.bind((mcast_addr, mcast_port))
    imr = _ip_mreqn(
            _in_addr.from_str(mcast_addr), _in_addr(socket.INADDR_ANY), ifindex
        )
    _socket.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, bytes(imr))
    if insecure:
        src = 'ANY SOURCE'
    else:
        src_port = util.get_nested(
                cfg, 'route', 'source_port', default=_DEF_SOURCE_PORT
            )
        _socket.connect((gateway, src_port))
        src = f'{gateway}:{src_port}'
    _LOG.info('Listening on {} for announcements from {} to {}:{}'.format(
              socket.if_indextoname(ifindex), src, mcast_addr, mcast_port));


def recv():
    msg, addr = _socket.recvfrom(256)
    msg_len = len(msg)
    _LOG.debug(f'Received {msg_len} bytes from {addr[0]}:{addr[1]}')
    if len(msg) != 4:
        _LOG.debug('Ignoring message due to incorrect length')
        msg = None
    else:
        msg = socket.inet_ntoa(msg)
    return msg


# kate: indent-width 4; replace-tabs on;
