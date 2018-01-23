#!/usr/bin/env python3
"""Models module."""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP
from sqlalchemy_utils.types import URLType, JSONType
import structlog


log = structlog.getLogger(__name__)
db = SQLAlchemy()
url_tags = db.Table(
    'url_tags',
    db.Column('url_id', db.Integer, db.ForeignKey('url_model.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True))
extracted_urls = db.Table(
    'extracted_urls',
    db.Column('url_set_id', db.Integer, db.ForeignKey('url_set.id'), primary_key=True),
    db.Column('url_id', db.Integer, db.ForeignKey('url_model.id'), primary_key=True))
search_model_urls = db.Table(
    'search_model_urls',
    db.Column('search_id', db.Integer, db.ForeignKey('search_model.id'), primary_key=True),
    db.Column('url_id', db.Integer, db.ForeignKey('url_model.id'), primary_key=True))
search_and_thread_sets = db.Table(
    'search_and_thread_sets',
    db.Column('search_id', db.Integer, db.ForeignKey('search_model.id'), primary_key=True),
    db.Column('thread_id', db.Integer, db.ForeignKey('thread_model.id'), primary_key=True))
search_model_json_data_sets = db.Table(
    'search_model_json_data_sets',
    db.Column('search_model_id', db.Integer, db.ForeignKey('search_model.id'), primary_key=True),
    db.Column('json_id', db.Integer, db.ForeignKey('json_data.id'), primary_key=True))
search_model_url_sets = db.Table(
    'search_model_url_sets',
    db.Column('search_model_id', db.Integer, db.ForeignKey('search_model.id'), primary_key=True),
    db.Column('url_set_id', db.Integer, db.ForeignKey('url_set.id'), primary_key=True))
url_json_data_sets = db.Table(
    'url_json_data_sets',
    db.Column('url_id', db.Integer, db.ForeignKey('url_model.id'), primary_key=True),
    db.Column('json_id', db.Integer, db.ForeignKey('json_data.id'), primary_key=True))
thread_model_json_data_sets = db.Table(
    'thread_model_json_data_sets',
    db.Column('thread_model_id', db.Integer, db.ForeignKey('thread_model.id'), primary_key=True),
    db.Column('json_id', db.Integer, db.ForeignKey('json_data.id'), primary_key=True))
url_set_json_data_sets = db.Table(
    'url_set_json_data_sets',
    db.Column('url_set_id', db.Integer, db.ForeignKey('url_set.id'), primary_key=True),
    db.Column('json_id', db.Integer, db.ForeignKey('json_data.id'), primary_key=True))


class DBVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, default=1, nullable=False)


class SearchModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    subreddit = db.Column(db.String, nullable=False)
    sort_mode = db.Column(db.String)
    time_mode = db.Column(db.String)
    page = db.Column(db.Integer, nullable=False)
    after_thread_id = db.Column(db.String)
    before_thread_id = db.Column(db.String)
    thread_models = relationship(
        'ThreadModel', secondary=search_and_thread_sets, lazy='subquery',
        backref=db.backref('search_models', lazy=True))
    json_data_list = relationship(
        'JSONData', secondary=search_model_json_data_sets, lazy='subquery',
        backref=db.backref('search_models', lazy=True))
    urls = relationship(
        'URLModel', secondary=search_model_urls, lazy='subquery',
        backref=db.backref('search_models', lazy=True))


class ThreadModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    thread_id = db.Column(db.String, nullable=False)
    url_id = db.Column(db.Integer, db.ForeignKey('url_model.id'))
    url = relationship(
        'URLModel', lazy='subquery',
        backref=db.backref('thread_models', lazy=True))
    json_data_list = relationship(
        'JSONData', secondary=thread_model_json_data_sets, lazy='subquery',
        backref=db.backref('thread_models', lazy=True))


class JSONData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    value = db.Column(JSONType)
    name = db.Column(db.String)


class URLModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    value = db.Column(URLType)
    tags = relationship(
        'Tag', secondary=url_tags, lazy='subquery',
        backref=db.backref('urls', lazy=True))
    json_data_list = relationship(
        'JSONData', secondary=url_json_data_sets, lazy='subquery',
        backref=db.backref('urls', lazy=True))

    def __repr__(self):
        templ = '<URLModel:{0.id} {0.value}>'
        return templ.format(self)


class NoExtractorURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    url_id = db.Column(db.Integer, db.ForeignKey('url_model.id'))
    url = relationship(
        'URLModel', lazy='subquery',
        backref=db.backref('no_extractor_models', lazy=True))


class DeniedURLFilter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    name = db.Column(db.String)
    regex = db.Column(db.String, nullable=False)

    def __repr__(self):
        name_field = '[{}] '.format(self.name) if self.name else ''
        templ = '<DeniedURLFilter:{0.id} {1}regex:{0.regex}>'
        return templ.format(self, name_field)


class URLSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('url_model.id'))
    url = relationship(
        'URLModel', lazy='subquery',
        backref=db.backref('url_sets', lazy=True))
    extracted_urls = relationship(
        'URLModel', secondary=extracted_urls, lazy='subquery',
        backref=db.backref('src_url_sets', lazy=True))
    json_data_list = relationship(
        'JSONData', secondary=url_set_json_data_sets, lazy='subquery',
        backref=db.backref('url_sets', lazy=True))


class Tag(db.Model):
    """Tag model."""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    namespace = db.Column(db.String)
    name = db.Column(db.String)

    def __repr__(self):
        templ = '<Tag:{0.id} {1}{0.name}>'
        return templ.format(self, '{}:'.format(self.namespace) if self.namespace else '')


def get_or_create(session, model, **kwargs):
    """Creates an object or returns the object if exists."""
    instance = session.query(model).filter_by(**kwargs).first()
    created = False
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
        created = True
    return instance, created
