# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

"""
InVirtualEnv Python Virtualenv Installer Module
"""
try:
    import pkg_resources
    __version__: str = pkg_resources.get_distribution("invirtualenv").version
except ImportError:
    ___version__ = '0.0.0'

__copyright__ = "Copyright 2016, Yahoo Inc."
__all__ = [
    'config',
    'contextmanager',
    'deploy',
    'exceptions',
    'package',
    'plugin',
    'plugin_base',
    'utility',
    'virtualenv'
]
