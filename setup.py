#!/usr/bin/env python
# coding: utf8
"""setup.py."""

import os
from setuptools import setup
from setuptools.command.test import test


# taken example from
# https://coderwall.com/p/qawuyq/use-markdown-readme-s-in-python-modules
HERE = os.path.dirname(__file__)
README_PATH = os.path.join(HERE, 'readme.md')
SHORT_DESCRIPTION = 'Downloads images from sub-reddits of reddit.com'
if os.path.isfile(README_PATH):
    with open(README_PATH) as _fo:
        LONG_DESCRIPTION = _fo.read()
else:
    LONG_DESCRIPTION = SHORT_DESCRIPTION

TESTS_REQUIRE = [
    'mock',
    'pytest',
    'tox'
]


class Tox(test):
    """Extend setuptools/distribute test command.

    It is used to trigger a test run when python setup.py test is issued.

    Taken from:
    https://tox.readthedocs.io/en/latest/example/basic.html
    """

    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        """initialize_options."""
        test.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        """finalize options."""
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        """run tests."""
        # import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        tox.cmdline(args=args)

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
    license='GNU General Public License v3 (GPLv3)',

    keywords="reddit image downloader",
    packages=['redditdownload'],
    entry_points={
        'console_scripts': [
            'redditdl.py = redditdownload.redditdownload:main',
        ],
    },
    install_requires=[
        'requests',
        'bs4',
        'lxml',
    ],
    tests_require=TESTS_REQUIRE,
    cmdclass={'test': Tox},
    extras_require={
        'recommended': [
            'html5lib',
            'Pillow', 'python-magic',
            'pyaux', 'yaml', 'ipython', 'atomicfile',
        ],
    },

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


if __name__ == '__main__':
    setup(**setup_kwargs)
