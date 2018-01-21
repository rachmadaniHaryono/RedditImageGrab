import re

from gallery_dl import job
from gallery_dl.extractor.message import Message
from redditdownload import models, reddit
import structlog


log = structlog.getLogger(__name__)


def get_or_create_search_model(subreddit, sort_mode=None, disable_cache=False, page=1):
    """get or create SearchModel."""
    session = models.db.session
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


def get_url(subreddit, sort_mode=None, index=1, disable_cache=False):
    log.warning('You are using unmaintained function. Please, use alternative function.')
    session = models.db.session
    norm_idx = index - 1
    url_ms = []
    m_q = session.query(models.SearchModel, models.URLModel).filter_by(
        subreddit=subreddit, sort_mode=sort_mode)
    if m_q.first():
        url_ms = []
        url_ms = [x[1] for x in m_q.all()]
        if norm_idx > len(url_ms):
            # TODO
            raise NotImplementedError
    else:
        reddit_data = reddit.getitems(subreddit, reddit_sort=sort_mode, return_raw_data=True)
        data_children = reddit_data['data'].pop('children')
        kwargs = {
            'subreddit': subreddit,
            'sort_mode': sort_mode,
            'page': 1,
            'after_thread_id': reddit_data['data']['after'],
            'before_thread_id': reddit_data['data']['before'],
        }
        m = models.SearchModel(**kwargs)
        thread_ms = []
        url_ms = []
        for x in data_children:
            thread_m = get_or_create_thread_model_from_json_data(x)[0]
            thread_ms.append(thread_m)
            url_ms.append(thread_m.url)
        m.thread_models.extend(thread_ms)
        json_data_m, _ = models.get_or_create(session, models.JSONData, value=reddit_data)
        m.json_data_list.append(json_data_m)
        session.add_all(thread_ms)
        session.add_all(url_ms)
        session.add(m)
        session.commit()
        if norm_idx > len(url_ms):
            # TODO
            raise NotImplementedError
    durl_filters = models.DeniedURLFilter.query.all()
    filtered_url_ms = []
    for url_m in url_ms:
        url_match = False
        for durl_filter in durl_filters:
            if re.match(durl_filter.regex, url_m.value):
                log.debug('url_filtered', url=url_m, filter_m=durl_filter)
                url_match = True
                break
        if not url_match:
            filtered_url_ms.append(url_m)
    return filtered_url_ms[norm_idx], {'total': len(filtered_url_ms)}


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


def get_or_create_url_set(url_model):
    session = models.db.session
    m, created = models.get_or_create(session, models.URLSet, url=url_model)
    if m:
        return m, created
    extracted_url_ms = []
    j = job.UrlJob(url_model.value)
    j.run()
    extractor_res = j.extractor
    log.debug('extraction', url=url_model, res=type(extractor_res))
    func_list = [
        func for func in dir(extractor_res)
        if callable(getattr(extractor_res, func)) and not func.startswith("__")
    ]
    log.debug('extractor funcs', flist=func_list)
    log.debug('extractor vars', v=vars(j.extractor))
    if hasattr(j.extractor, 'items') and not url_model.json_data_list:
        items = list(j.extractor.items())
        non_url_json_data_list = [x for x in items if x[0] != Message.Url]
        url_json_data_list = [x for x in items if x[0] == Message.Url]
        for item in url_json_data_list:
            extracted_url_m = models.get_or_create(session, models.URLModel, value=item[1])[0]
            if item[2]:
                extracted_url_m.json_data_list.append(
                    models.get_or_create(session, models.JSONData, value=item[2])[0])
            extracted_url_ms.append(extracted_url_m)
        url_model.json_data_list.append(
            models.get_or_create(session, models.JSONData, value=non_url_json_data_list)[0]
        )
    if extracted_url_ms:
        m.extend(extracted_url_ms)
        created = True
    session.add(m)
    return m, created


def get_or_create_extracted_urls(url_model):
    log.warning('You are using unmaintained function. Please, use alternative function.')
    instance = models.URLSet.query.filter_by(url=url_model).first()
    created = False
    extracted_url_ms = []
    session = models.db.session
    if instance:
        return instance.extracted_urls, created
    j = job.UrlJob(url_model.value)
    j.run()
    extractor_res = j.extractor
    log.debug('extraction', url=url_model, res=type(extractor_res))
    func_list = [
        func for func in dir(extractor_res)
        if callable(getattr(extractor_res, func)) and not func.startswith("__")
    ]
    log.debug('extractor funcs', flist=func_list)
    log.debug('extractor vars', v=vars(j.extractor))
    if hasattr(j.extractor, 'items') and not url_model.json_data_list:
        items = list(j.extractor.items())
        non_url_json_data_list = [x for x in items if x[0] != Message.Url]
        url_json_data_list = [x for x in items if x[0] == Message.Url]
        for item in url_json_data_list:
            extracted_url_m = models.get_or_create(session, models.URLModel, value=item[1])[0]
            if item[2]:
                extracted_url_m.json_data_list.append(
                    models.get_or_create(session, models.JSONData, value=item[2])[0])
            extracted_url_ms.append(extracted_url_m)
        url_model.json_data_list.append(
            models.get_or_create(session, models.JSONData, value=non_url_json_data_list)[0]
        )
    if extracted_url_ms:
        url_set_m = models.URLSet(url=url_model, extracted_urls=extracted_url_ms)
        session.add(url_set_m)
        session.commit()
        created = True
    session.add(url_model)
    return extracted_url_ms, created
