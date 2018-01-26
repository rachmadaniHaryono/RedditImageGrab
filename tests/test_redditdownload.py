#!/usr/bin/env python
"""test redditdownload module."""
from os import getcwd
from unittest import mock, TestCase
import json
import os
import sys
import unittest

import pytest

from redditdownload import redditdownload
from redditdownload.redditdownload import download_from_url, parse_args, process_imgur_url

FILE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files')


def get_mock_items():
    """get mock items."""
    items_json_path = os.path.join(FILE_FOLDER, 'items.json')
    with open(items_json_path) as ff:
        mock_items = json.load(ff)
    return mock_items


class TestMainMethod(unittest.TestCase):
    """test the main function of redditdownload module."""

    def test_no_input(self):
        """test no input when main func called.

        program will exit for this case.
        """
        with pytest.raises(SystemExit):
            redditdownload.main()

    @mock.patch('redditdownload.redditdownload.download_from_url')
    @mock.patch('redditdownload.redditdownload.getitems', side_effect=[get_mock_items(), {}])
    def test_update_flag(self, mock_get_items, mock_download_func):
        """test update flag.

        it test if update flag is raised properly and if get_items func will call twice,
        because download_func only raise FileExistsException."""
        test_argv = ['redditdl.py', 'cats', '--num', '2', '--update']
        with mock.patch.object(sys, 'argv', test_argv):
            # run the main function.
            redditdownload.main()

            # assert the call count
            assert mock_get_items.call_count == 1
            assert mock_download_func.call_count == 2

            # change side effect to raise error
            err_txt = 'Expected Error on testing'
            mock_download_func.side_effect = redditdownload.FileExistsException(err_txt)
            # run the main func.
            redditdownload.main()

            # assert the call count
            assert mock_get_items.call_count == 2
            assert mock_download_func.call_count == 2


class TestDownloadFromURLMethods(unittest.TestCase):

    @mock.patch('redditdownload.redditupload.download')
    @mock.patch('redditdownload.redditdownload.pathexists')
    def test_download_from_url(self, mock_pathexist, mock_download_func):
        """test :func:`download_from_url`."""
        # set mock value
        mock_url = (
            'https://i.reddituploads.com/aaa5af49dea641718b1428d7b0c46bec'
            '?fit=max&h=1536&w=1536&s=6f08d532dc8e81ea8d4a85e6cac643b2')
        mock_dest_file = mock.Mock()
        mock_pathexist.return_value = False

        download_from_url(mock_url, mock_dest_file)

        mock_pathexist.assert_called_once_with(mock_dest_file)
        mock_download_func.assert_called_once_with(mock_url, mock.ANY)


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
