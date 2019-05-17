#!/usr/bin/env python
# Copyright (c) 2016, Yahoo Inc.
# Copyrights licensed under the BSD License
# See the accompanying LICENSE.txt file for terms.

import os
import json
from setuptools import setup


def scripts():
    """
    Get a list of the scripts in the scripts directory

    Returns
    -------
    list
        A list of strings containing the scripts in the scripts directory
    """
    script_list = []

    if os.path.isdir('scripts'):
        script_list += [
            os.path.join('scripts', f) for f in os.listdir('scripts')
        ]
    return script_list


if __name__ == '__main__':
    version = '1.0.0'
    setup(
        package_data= {
            'invirtualenv': [
                'package_metadata.json',
            ],
            'invirtualenv_plugins': [
                'docker_scripts/*'
            ]
        },
        scripts= scripts(),
    )
