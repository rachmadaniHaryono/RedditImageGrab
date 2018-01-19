from redditdownload import models, reddit


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
            pass
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
            pass
    return url_ms[norm_idx]


def get_urls(subreddit, minimum=1, sort_mode=None, disable_cache=False):
    pass


def get_or_create_thread_model_from_json_data(json_data):
    json_data_m, _ = models.get_or_create(models.db.session, models.JSONData, value=json_data)
    url_m, _ = models.get_or_create(models.db.session, models.URLModel, value=json_data['data']['url'])
    kwargs = {'thread_id': json_data['data']['id']}
    m, created = models.get_or_create(models.db.session, models.ThreadModel, **kwargs)
    m.url = url_m
    m.json_data = json_data_m
    return m, created
