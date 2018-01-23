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
