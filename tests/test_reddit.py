"""test reddit module."""
from unittest import mock
from urllib.error import HTTPError
import itertools
import logging

import pytest
import vcr

from redditdownload.reddit import getitems


logging.basicConfig()
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.INFO)


@vcr.use_cassette()
def test_empty_string(caplog):
    """test empty string but with mocking external dependencies.

    it will result the following url which
    https://www.reddit.com/r/.json
    which will redirect to json version of this url
    https://www.reddit.com/subreddits
    """
    res = getitems("")
    assert caplog.records[0].name == 'redditdownload.reddit'
    assert caplog.records[0].msg == 'url:http://www.reddit.com/r/.json'
    assert len(res) == 25
    assert res[0]['url'] == '/r/AskReddit/'


def get_parameter_for_test_sort_type():
    # sort_type none, input is multireddit
    res = [
        # sort_type none, input is multireddit
        (
            {'subreddit': 'some_user/m/some_multireddit', 'reddit_sort': None, 'multireddit': True, },
            {
                'record_msgs': [
                    'url:http://www.reddit.com/user/some_user/m/some_multireddit.json',
                    "data: {'message': 'Not Found', 'error': 404}"
                ],
                'error': KeyError,
            }
        ),
        # starting with none sort_type
        (
            {'subreddit': 'cats', 'reddit_sort': None, },
            {'record_msgs': ['url:http://www.reddit.com/r/cats.json'], }
        ),
    ]
    # test with sort type
    for sort_type in ['hot', 'new', 'rising', 'controversial', 'top', 'gilded']:
        res.append((
            {'subreddit': 'cats', 'reddit_sort': sort_type},
            {'record_msgs': ['url:http://www.reddit.com/r/cats/{}.json'.format(sort_type)]}
        ))

    for sort_type in ['controversial']:  # , 'top']:
        for time_limit in ['hour']:  # , 'day', 'week', 'month', 'year', 'all']:
            reddit_sort = sort_type + time_limit
            res.append((
                {'subreddit': 'cats', 'reddit_sort': reddit_sort},
                {'record_msgs': [
                    'url:http://www.reddit.com/r/cats/{0}.json?sort={0}&t={1}'.format(
                        sort_type, time_limit
                    ),
                ]}
            ))
    return res


@pytest.mark.parametrize("test_input, data", get_parameter_for_test_sort_type())
@vcr.use_cassette(record_mode='new_episodes')
def test_sort_type(caplog, test_input, data):
    """test sort_type."""
    error = data.get('error', None)
    if error:
        with pytest.raises(error):
            getitems(**test_input)
    else:
        getitems(**test_input)
    filtered_records = list(filter(lambda x: x.name == 'redditdownload.reddit', caplog.records))
    record_msgs = [x.msg for x in filtered_records]
    assert record_msgs == data['record_msgs']


def get_parameter_for_test_advanced_sort_and_last_id():
    last_id = '44h81z'
    time_limits = ['hour', 'day', 'week', 'month', 'year', 'all']
    test_input = itertools.product(['controversial', 'top'], time_limits)
    templ = 'http://www.reddit.com/r/cats/{0}.json?after=t3_{2}&sort={0}&t={1}'
    res = [
        [
            (x[0], x[1], last_id),
            templ.format(x[0], x[1], last_id)
        ]
        for x in test_input
    ]
    return res


@pytest.mark.parametrize("test_input, data", get_parameter_for_test_advanced_sort_and_last_id())
@vcr.use_cassette(record_mode='new_episodes')
def test_advanced_sort_and_last_id(caplog, test_input, data):
    """test for advanced sort and last id."""
    reddit_sort = test_input[0] + test_input[1]
    res = getitems('cats', reddit_sort=reddit_sort, previd=test_input[2])
    filtered_records = \
        list(filter(lambda x: x.name == 'redditdownload.reddit', caplog.records))
    record_msgs = [x.msg for x in filtered_records]
    assert record_msgs == ['url:{}'.format(data)]
    assert len(res) in [25, 0]


@mock.patch('redditdownload.reddit.requests.get')
def test_raise_error_on_request(m_get):
    """test when error raised on requests."""
    errors = [
        HTTPError(None, 404, 'mock error', None, None), KeyboardInterrupt]
    for error in errors:
        m_get.side_effect = error
        with pytest.raises(SystemExit):
            getitems('cats')


@mock.patch('redditdownload.reddit.requests.get')
def test_value_error_on_request(m_get):
    """test value error on requests."""
    m_get.side_effect = ValueError('Mock error')
    with pytest.raises(ValueError):
        getitems('cats')

    # value error contain specific message which raise other error.
    msg = 'No JSON object could be decoded'
    m_get.side_effect = ValueError(msg)
    with pytest.raises(SystemExit):
        getitems('cats')


def test_error_on_multireddit_input():
    """test wrong multireddit flag on multireddit input."""
    # multireddit flag raised but input is normal subreddit
    with pytest.raises(SystemExit):
        getitems('cats', multireddit=True)

    # multireddit input given but multireddit flag is False
    with pytest.raises(SystemExit):
        getitems('someuser/m/some_multireddit', multireddit=False)
