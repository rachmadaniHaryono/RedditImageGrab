from urllib.parse import urljoin
import queue
import re

from gallery_dl.exception import NoExtractorError, AuthenticationError
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
    if page != 1:
        raise NotImplementedError('Only work for first page.')
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
    permalink_m_value = urljoin('https://www.reddit.com', json_data['data']['permalink'])
    permalink_m, m = models.get_or_create(models.db.session, models.URLModel, value=permalink_m_value)
    kwargs = {'thread_id': json_data['data']['id']}
    m, created = models.get_or_create(models.db.session, models.ThreadModel, **kwargs)
    if created:
        m.json_data = json_data_m
        m.permalink = permalink_m
        m.url = url_m
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


def get_or_create_url_sets_from_extractor_job(job, url_model=None, session=None):
    session = models.db.session if session is None else session
    if url_model is None:
        url_m, _ = models.get_or_create(session, models.URLModel, value=job.url)
    else:
        url_m = url_model
    for msg in job.data:
        msg_id = str(msg[0])
        # log.debug('processed msg', msg=msg)
        if msg_id in [models.MESSAGE_VERSION, models.MESSAGE_DIRECTORY]:
            m, created = models.get_or_create(session, models.URLSet, url=url_m, set_type=msg_id)
            if created and msg[1]:
                m.json_data = models.get_or_create(session, models.JSONData, value=msg[1])[0]
        elif msg_id in [models.MESSAGE_URL, models.MESSAGE_QUEUE]:
            kwargs = dict(set_type=msg_id, url=url_m)
            if msg[1] != url_m.value:
                eurl_m = models.get_or_create(session, models.URLModel, value=msg[1])[0]
                kwargs['extracted_url'] = eurl_m
                session.add(eurl_m)
            m, created = models.get_or_create(session, models.URLSet, **kwargs)
            if created and msg[2]:
                m.json_data = models.get_or_create(session, models.JSONData, value=msg[2])[0]
        elif msg_id == models.MESSAGE_URLLIST:
            eurl_ms = []
            for url in msg[1]:
                if url != url_m.value:
                    eurl_m = models.get_or_create(session, models.URLModel, value=url)
                    session.add(eurl_m)
                else:
                    eurl_m = url_m
                eurl_ms.append(eurl_m)
            m, created = models.get_or_create(
                session, models.URLSet, url=url_m, set_type=msg_id)
            if created:
                m.extracted_urls = eurl_ms
                m.json_data = models.get_or_create(session, models.JSONData, value=msg[2])[0]
            elif not created and m.extracted_urls == eurl_ms:
                m.json_data = models.get_or_create(session, models.JSONData, value=msg[2])[0]
            else:
                raise NotImplementedError
        else:
            raise ValueError('Unknown message type: {}'.format(msg_id))
        session.add(m)
        yield m, created


def get_search_result_on_index_page(subreddit, session=None, page=1, disable_cache=False, sort_mode=None):
    session = models.db.session if session is None else session
    search_model, search_model_created = get_or_create_search_model(
        subreddit, sort_mode=sort_mode, disable_cache=disable_cache, page=page, session=session)
    session.add(search_model)
    # collect all url models
    url_ms = [x.url for x in search_model.thread_models]
    url_ms.extend([x.permalink for x in search_model.thread_models])
    url_ms = list(set(url_ms))
    q = queue.Queue()
    list(map(lambda x: q.put(x), url_ms))
    processed_url_ms = []
    while not q.empty():
        url_m = q.get()
        if not url_m:
            log.debug('empty url model', url_model=url_m)
            continue
        processed_url_ms.append(url_m)
        is_url_filtered = not bool(list(filter_url_models([url_m])))
        if is_url_filtered:
            continue
        instances = session.query(models.URLSet).filter_by(url=url_m).all()
        if instances:
            url_sets_from_job = instances
        else:
            try:
                j = CacheJob(url_m.value)
                log.debug('processing url', url_m=url_m)
            except NoExtractorError as e:
                log.debug('No extractor', url_m=url_m, e=e)
                ne_url_m = models.get_or_create(session, models.NoExtractorURL, url=url_m)[0]
                session.add(ne_url_m)
                continue
            try:
                j.run()
            except AuthenticationError as e:
                log.debug('No extractor', url_m=url_m, e=e)
                continue
            # deduplicate data
            data_set = []
            [data_set.append(x) for x in j.data if x not in data_set]
            j.data = data_set
            # data
            url_sets_from_job = [
                x for x, _ in list(sorted(
                    get_or_create_url_sets_from_extractor_job(job=j),
                    key=lambda k: k[0].extracted_url.value if k[0].extracted_url else ''
                ))
            ]

        for item in url_sets_from_job:
            if item.extracted_url not in processed_url_ms and item.extracted_url:
                processed_url_ms.append(item.extracted_url)
                log.debug('added to queue', item=item.extracted_url)
                q.put(item.extracted_url)
        yield (url_m, url_sets_from_job)
