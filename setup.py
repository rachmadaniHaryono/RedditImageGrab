#!/usr/bin/env python
# coding: utf8

import os
from setuptools import setup
from setuptools.command.test import test


# taken example from
# https://coderwall.com/p/qawuyq/use-markdown-readme-s-in-python-modules
SHORT_DESCRIPTION = 'Downloads images from sub-reddits of reddit.com.'
# fall back when long description is not found.
LONG_DESCRIPTION = SHORT_DESCRIPTION
if os.path.exists('README.txt'):
    LONG_DESCRIPTION = open('README.txt').read()

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
    packages=['redditdownload'],
    entry_points={
        'console_scripts': [
            'redditdl.py = redditdownload.redditdownload:main',
        ],
    },
    install_requires=[
        # Actually, most of the dependencies are optional.
    ],
    tests_require=TESTS_REQUIRE,
    cmdclass={'test': Tox},
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
