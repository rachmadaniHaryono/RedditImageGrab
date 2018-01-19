import copy

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


@vcr.use_cassette()
@pytest.mark.parametrize(
    "test_input, data",
    [
        ({'idx': 1}, {'id': 1, 'value': 'https://i.redd.it/sq26seiyhua01.jpg'})
    ]
)
def test_get_url(tmp_db, test_input, data):
    res = api.get_url('cats', index=test_input['idx'])
    assert res.id == data['id']
    assert res.value == data['value']
    res2 = api.get_url('cats')
    assert res2.id == data['id']
    assert res2.value == data['value']
