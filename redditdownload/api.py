import re

from gallery_dl.extractor.message import Message
from gallery_dl.exception import NoExtractorError
from gallery_dl.job import Job
from redditdownload import models, reddit
import structlog


log = structlog.getLogger(__name__)


class CacheJob(Job):

    def __init__(self, url, parent=None):
        Job.__init__(self, url, parent)
        self.data = []

    def run(self):
        self.data = [msg for msg in self.extractor]


def get_or_create_search_model(subreddit, sort_mode=None, disable_cache=False, page=1, session=None):
    """get or create SearchModel."""
    session = models.db.session if session is None else session
    m, created = models.get_or_create(session, models.SearchModel, subreddit=subreddit, sort_mode=sort_mode, page=page)
    if created:
        reddit_data = reddit.getitems(subreddit, reddit_sort=sort_mode, return_raw_data=True)
        data_children = reddit_data['data'].pop('children')
        json_data_m = models.get_or_create(session, models.JSONData, value=reddit_data)[0]
        m.json_data_list.append(json_data_m)
        # processing data_children
        thread_ms = []
        for item in data_children:
            thread_m = get_or_create_thread_model_from_json_data(item)[0]
            thread_ms.append(thread_m)
        m.thread_models.extend(thread_ms)
        session.add(m)
    return m, created


def filter_url_models(url_models):
    durl_filters = models.DeniedURLFilter.query.all()
    for url_m in url_models:
        url_match = False
        for durl_filter in durl_filters:
            if re.match(durl_filter.regex, url_m.value):
                log.debug('url_filtered', url=url_m, filter_m=durl_filter)
                url_match = True
                break
        if not url_match:
            yield url_m


def get_or_create_thread_model_from_json_data(json_data):
    json_data_m, _ = models.get_or_create(models.db.session, models.JSONData, value=json_data)
    url_m, _ = models.get_or_create(models.db.session, models.URLModel, value=json_data['data']['url'])
    kwargs = {'thread_id': json_data['data']['id']}
    m, created = models.get_or_create(models.db.session, models.ThreadModel, **kwargs)
    m.url = url_m
    m.json_data = json_data_m
    return m, created


def get_or_create_url_set(session, url, extracted_urls):
    URLSet = models.URLSet
    instances = session.query(models.URLSet).filter(
        URLSet.url == url).all()
    match_instances = [x for x in instances if x == extracted_urls]
    instance = next(iter(match_instances or []), None)
    created = False
    if not instance:
        instance = URLSet(url=url, extracted_urls=extracted_urls)
        session.add(instance)
        created = True
    return instance, created


def get_or_create_url_sets(subreddit, session=None, page=1, per_page=0, disable_cache=False, sort_mode=None):
    session = models.db.session if session is None else session
    res = []
    if per_page == 0:
        search_model, search_model_created = get_or_create_search_model(
            subreddit, sort_mode=sort_mode, disable_cache=disable_cache, page=page, session=session)
    else:
        raise NotImplementedError
    if search_model.urls:
        for url_m in search_model.urls:
            for url_set_m in url_m.url_sets:
                res.append([url_set_m, False])
        return res
    url_ms = [x.url for x in search_model.thread_models]
    if per_page == 0:
        filtered_url_ms = list(filter_url_models(url_ms))
        new_url_ms = []
        for url_m in filtered_url_ms:
            is_url_filtered = not bool(list(filter_url_models([url_m])))
            if is_url_filtered:
                continue
            log.debug('processing url', url_m=url_m)
            try:
                j = CacheJob(url_m.value)
            except NoExtractorError as e:
                log.debug('No extractor', url_m=url_m, e=e)
                models.get_or_create(session, models.NoExtractorURL, url=url_m)
                continue
            j.run()
            message_urllist_type = Message.Urllist if hasattr(Message, 'Urllist') else 7
            for msg in j.data:
                log.debug('processing msg', msg=msg)
                if msg[0] == Message.Version:
                    pass
                elif msg[0] == Message.Directory:
                    url_m.json_data_list.append(models.get_or_create(session, models.JSONData, value=msg)[0])
                elif msg[0] == Message.Url:
                    e_m, _ = models.get_or_create(session, models.URLModel, value=msg[1])
                    if not bool(list(filter_url_models([e_m]))):
                        continue
                    if msg[2]:
                        e_m.json_data_list.append(models.get_or_create(session, models.JSONData, value=msg[2])[0])
                    res.append(get_or_create_url_set(session, url=url_m, extracted_urls=[e_m]))
                elif msg[0] == message_urllist_type:
                    e_ms = []
                    for msg_url in msg[1]:
                        e_m = models.get_or_create(session, models.URLModel, value=msg[1])[0]
                        if not bool(list(filter_url_models([e_m]))):
                            continue
                        e_ms.append()
                    url_list_url_set_model, url_list_url_set_model_created = \
                        get_or_create_url_set(session, url=url_m, extracted_urls=e_ms)
                    if msg[2]:
                        url_list_url_set_model.json_data_list.append(
                            models.get_or_create(session, models.JSONData, value=msg[2])[0])
                    res.append(url_list_url_set_model, url_list_url_set_model_created)
                elif msg[0] == Message.Queue:
                    e_m, _ = models.get_or_create(session, models.URLModel, value=msg[1])
                    if not bool(list(filter_url_models([e_m]))):
                        continue
                    if msg[2]:
                        e_m.json_data_list.append(models.get_or_create(session, models.JSONData, value=msg[2])[0])
                    res.append(get_or_create_url_set(session, url=url_m, extracted_urls=[e_m]))
                    url_ms.append(e_m)
                    new_url_ms.append(e_m)
                else:
                    raise ValueError('Unknown message type:{}'.format(msg[0]))
        if url_ms:
            url_ms = set(url_ms)
            search_model.urls.extend(x for x in url_ms if x not in search_model.urls)
            session.add(search_model)
    else:
        raise NotImplementedError
    return res
