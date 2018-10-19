#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

packages = [
    'abr', 'abr.app', 'abr.parsers',
]

package_data = {
    'abr': ['*.enaml', 'data/*'],
}

requires = [
    'numpy',
    'matplotlib',
    'scipy',
    'pandas',
    'enaml',
    'tables',
]

classifiers = [
        'Operating System :: OS Independent',
        'Programming Language :: Python',
]

setup(
    name='ABR',
    description='ABR wave analyzer',
    version='0.1.0',
    long_description=readme,
    packages=find_packages(),
    package_data=package_data,
    install_requires=requires,
    classifiers=classifiers,
    entry_points={
        'console_scripts': [
            'abr_gui = abr.app.cmd_main:main',
            'abr_loop = abr.app.cmd_main_loop:main',
        ]
    },
)
