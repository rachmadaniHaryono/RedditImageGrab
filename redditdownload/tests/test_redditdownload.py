#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
from unittest import TestCase
from os import getcwd

from redditdownload import parse_args, process_deviant_url, process_imgur_url


class TestParseArgs(TestCase):
    def test_simple_args(self):
        ARGS = parse_args(['funny'])
        self.assertEqual(ARGS.reddit, 'funny')
        self.assertEqual(ARGS.dir, getcwd())

    def test_multiple_reddit_plus(self):
        ARGS = parse_args(['funny+anime'])
        self.assertEqual(ARGS.reddit, 'funny+anime')

    def test_nsfw_sfw_arg(self):
        ARGS = parse_args(['--nsfw --sfw'])
        self.assertFalse(ARGS.nsfw)
        self.assertFalse(ARGS.sfw)


class TestProcessImgurUrl(TestCase):
    def setUp(self):
        self.album_url = 'http://imgur.com/a/WobUS'
        self.album_url_member = 'http://i.imgur.com/qVOLIba.jpg'

        # single url with extension
        self.single_url = 'https://i.imgur.com/XdWGz14.jpg'

    def test_extract_album(self):
        result = process_imgur_url(self.album_url)
        self.assertIsInstance(result, list)
        self.assertIn(self.album_url_member, result)

    def test_extract_single(self):
        result = process_imgur_url(self.single_url)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn(self.single_url, result)

if __name__ == '__main__':
    unittest.main()
