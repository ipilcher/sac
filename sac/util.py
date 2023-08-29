# SPDX-License-Identifier:  GPL-3.0-or-later

#
#       SAC - Source Address Client
#
#	Utility functions
#
#       Copyright 2023 Ian Pilcher <arequipeno@gmail.com>
#


def get_nested(cfg, *keys, default=None):
    """Get a nested configuration item (``default`` if any key is missing)."""
    c = cfg
    for k in keys:
        if c is None:
            break
        c = c.get(k)
    return c if c is not None else default


# kate: indent-width 4; replace-tabs on;
