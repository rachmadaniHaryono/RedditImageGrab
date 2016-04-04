#!/usr/bin/env python
"""setup to install module."""

from os import path, getcwd
from setuptools import setup, find_packages

from redditdownload import __version__ as version

with open(path.join(getcwd(), 'readme.md')) as f:
    long_description = f.read()


setup(
    name='RedditImageGrab',
    version=version,
    description='Downloads JPEG images from sub-reddits of reddit.com',
    long_description=long_description,
    packages=find_packages(),
    package_data={'': ['*.md']},
    entry_points={'console_scripts': ['redditdl=redditdownload.redditdownload:main']},
    # metadata for upload to PyPI
    author='HoverHell',
    author_email='hoverhell@gmail.com',
    license='GNU General Public License v3 (GPLv3)',
    keywords="reddit image downloader",
    url='https://github.com/HoverHell/RedditImageGrab',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Topic :: Terminals',
        ],
    )
