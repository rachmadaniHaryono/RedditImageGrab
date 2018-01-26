from flask import Flask
import pytest
import structlog
import vcr

from redditdownload import models, api


log = structlog.getLogger(__name__)


@pytest.fixture()
def tmp_db(tmpdir):
    """Get tmp db."""
    app = Flask(__name__)
    tmp_db_path = tmpdir.join('temp.db')
    log.debug('db path', v=tmp_db_path)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + tmp_db_path.strpath
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    models.db.init_app(app)
    app.app_context().push()
    models.db.create_all()
    return models.db


@pytest.mark.no_travis
@vcr.use_cassette(record_mode='new_episodes')
def test_get_or_create_url_sets(tmp_db):
    res = api.get_or_create_url_sets('cats', session=tmp_db.session)
    assert all([x[1] for x in res])
    tmp_db.session.add_all([x[0] for x in res])
    tmp_db.session.commit()
    res2 = api.get_or_create_url_sets('cats', session=tmp_db.session)
    assert all([not x[1] for x in res2])
    tmp_db.session.add_all([x[0] for x in res2])
    tmp_db.session.commit()


@pytest.mark.no_travis
@vcr.use_cassette(record_mode='new_episodes')
def test_get_or_create_url_sets_from_extractor_job(tmp_db):
    url = 'https://www.reddit.com/r/anime/comments/7sri38/happy_10th_anniversary_ranime'
    j = api.CacheJob(url)
    j.run()
    data_set = []
    [data_set.append(x) for x in j.data if x not in data_set]
    j.data = data_set
    res = list(api.get_or_create_url_sets_from_extractor_job(job=j))
    assert res
    assert all(x[0] for x in res)
    assert len(res) < 78


@pytest.mark.no_travis
@vcr.use_cassette(record_mode='new_episodes')
def test_get_or_create_search_model(tmp_db):
    res = api.get_or_create_search_model('cats')
    assert res


@pytest.mark.no_travis
@vcr.use_cassette(record_mode='new_episodes')
def test_get_search_result_on_index_page(tmp_db):
    res = list(api.get_search_result_on_index_page(subreddit='anime'))
    assert res
