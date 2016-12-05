#!/usr/local/bin/python3

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Toolchain for analysing muon neutrinos within the energy \
                    range of 1-1000 GeV with IceCube DeepCore.',
    'author': 'Philipp Schlunder',
    'url': 'https://github.com/WortPixel/phd_scripts',
    'download_url': 'https://github.com/WortPixel/phd_scripts/archive/master.zip',
    'author_email': 'philipp.schlunder@udo.edu',
    'version': '0.1',
    'install_requires': ['matplotlib',
                         'numpy',
                         'pandas',
                         'paramiko',
                         'pypet',
                         'scipy',
                         'sklearn',
                         'tables',
                         'tqdm',
                         ],
    'packages': ['nuance',
                 'nuance.data_handler',
                 'nuance.icetray_modules',
                 'nuance.job_handler'],
    'scripts': [],
    'name': 'nuance'
}

setup(**config)
