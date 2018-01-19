import re

from gallery_dl import job, extractor
from redditdownload import models, reddit
import structlog


log = structlog.getLogger(__name__)


def get_url(subreddit, sort_mode=None, index=1, disable_cache=False):
    norm_idx = index - 1
    url_ms = []
    m_q = models.db.session.query(models.SearchModel, models.URLModel).filter_by(
        subreddit=subreddit, sort_mode=sort_mode)
    if m_q.first():
        url_ms = []
        url_ms = [x[1] for x in m_q.all()]
        if norm_idx > len(url_ms):
            # TODO
            raise NotImplementedError
    else:
        reddit_data = reddit.getitems(subreddit, reddit_sort=sort_mode, return_raw_data=True)
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
        for x in reddit_data['data']['children']:
            thread_m = get_or_create_thread_model_from_json_data(x)[0]
            thread_ms.append(thread_m)
            url_ms.append(thread_m.url)
        m.thread_models.extend(thread_ms)
        models.db.session.add_all(thread_ms)
        models.db.session.add_all(url_ms)
        models.db.session.add(m)
        models.db.session.commit()
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


def get_or_create_thread_model_from_json_data(json_data):
    json_data_m, _ = models.get_or_create(models.db.session, models.JSONData, value=json_data)
    url_m, _ = models.get_or_create(models.db.session, models.URLModel, value=json_data['data']['url'])
    kwargs = {'thread_id': json_data['data']['id']}
    m, created = models.get_or_create(models.db.session, models.ThreadModel, **kwargs)
    m.url = url_m
    m.json_data = json_data_m
    return m, created


def get_or_create_extracted_urls(url_model):
    instance = models.URLSet.query.filter_by(url=url_model).first()
    created = False
    extracted_url_ms = []
    if not instance:
        j = job.UrlJob(url_model.value)
        j.run()
        extractor_res = j.extractor
        log.debug('extraction', url=url_model, res=extractor_res)
        # import pdb; pdb.set_trace()
        if isinstance(j.extractor, extractor.reddit.RedditSubmissionExtractor) and not url_model.json_data_list:
            json_data_value = j.extractor.submissions()[0][0]
            json_data_m, _ = models.get_or_create(
                models.db.session, models.JSONData, value=json_data_value)
            url_model.json_data_list.append(json_data_m)
            models.db.session.add(url_model)
            models.db.session.commit()
        else:
            # TODO
            raise NotImplementedError
    return extracted_url_ms, created
