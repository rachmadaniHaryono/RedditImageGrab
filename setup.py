#!/usr/bin/env python
# coding: utf8
"""setup.py."""

import os
from setuptools import setup


HERE = os.path.dirname(__file__)
README_PATH = os.path.join(HERE, 'readme.md')
SHORT_DESCRIPTION = 'Downloads images from sub-reddits of reddit.com'
if os.path.isfile(README_PATH):
    with open(README_PATH) as _fo:
        LONG_DESCRIPTION = _fo.read()
else:
    LONG_DESCRIPTION = SHORT_DESCRIPTION


setup_kwargs = dict(
    name='redditdownload',
    version='1.5',
    description=SHORT_DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    # classifiers=[],
    # keywords='...,...',
    author='HoverHell',
    author_email='hoverhell@gmail.com',
    url='https://github.com/HoverHell/RedditImageGrab',
    packages=['redditdownload'],
    entry_points={
        'console_scripts': [
            'redditdl.py = redditdownload.redditdownload:main',
        ],
    },
    install_requires=[
        # Actually, most of the dependencies are optional.
    ],
    extras_require={
        'recommended': [
            'beautifulsoup4', 'lxml', 'html5lib',
            'requests',
            'Pillow', 'python-magic',
            'pyaux', 'yaml', 'ipython', 'atomicfile',
        ],
    }
)


if __name__ == '__main__':
    setup(**setup_kwargs)
