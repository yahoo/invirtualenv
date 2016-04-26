# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
InVirtualEnv Python Virtualenv Installer Module
"""
import json
import os
import sys


__copyright__ = "Copyright 2016, Yahoo Inc."
__directory__ = os.path.dirname(__file__)
__version__ = '0.0.0'

if hasattr(sys, "_MEIPASS"):
    __directory__ = sys._MEIPASS  # pylint: disable=E1101,W0212

__metadata_filename__ = os.path.join(__directory__, 'package_metadata.json')
if os.path.exists(__metadata_filename__):
    with open(__metadata_filename__) as __metadata_handle:
        __metadata__ = json.load(__metadata_handle)
        __version__ = __metadata__['version']

del __metadata_filename__

__all__ = [
    'config',
    'deploy',
    'exceptions',
    'package',
    'plugin',
    'static',
    'utility',
    'virtualenv'
]
