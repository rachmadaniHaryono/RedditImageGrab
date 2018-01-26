#!/usr/bin/python3
import os
import logging
import pprint

from flask import Flask
from flask.cli import FlaskGroup
from flask_admin import Admin  # , BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_debugtoolbar import DebugToolbarExtension
import click

from redditdownload import views, models


def create_app(script_info=None):
    app = Flask(__name__)
    debug = app.config['DEBUG'] = bool(os.getenv('REDDITDL_DEBUG')) or app.config['DEBUG']
    reloader = app.config['TEMPLATES_AUTO_RELOAD'] = \
        bool(os.getenv('REDDITDL_RELOADER')) or app.config['TEMPLATES_AUTO_RELOAD']
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        os.getenv('REDDITDL_SQLALCHEMY_DATABASE_URI') or 'sqlite:///redditdownload.db'
    app.config['SECRET_KEY'] = os.getenv('REDDITDL_SERVER_SECRET_KEY') or os.urandom(24)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    if reloader:
        app.jinja_env.auto_reload = True
    if debug:
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        app.config['LOGGER_HANDLER_POLICY'] = 'debug'
        app.debug = True  # additional step, may not work
        logging.basicConfig(level=logging.DEBUG)
        pprint.pprint(app.config)
        DebugToolbarExtension(app)
    models.db.init_app(app)
    app.app_context().push()
    models.db.create_all()

    @app.shell_context_processor
    def shell_context():
        return {'app': app, 'db': models.db}

    admin_templ = 'redditdownload/index.html'
    session = models.db.session
    app_admin = Admin(
        app, name='Reddit Images Download', template_mode='bootstrap3',
        index_view=views.HomeView(name='Home', template=admin_templ, url='/'))
    app_admin.add_view(views.URLView(name='URL Viewer', endpoint='u'))
    app_admin.add_view(views.SearchModelView(models.SearchModel, session, name='Search History'))
    app_admin.add_view(views.URLModelView(models.URLModel, session, name='URL History'))
    app_admin.add_view(views.JSONDataView(models.JSONData, session, name='JSON Data'))
    model_list = [
        (models.DeniedURLFilter, 'URL Filter'),
        (models.URLSet, 'URL Set'),
        # (models.JSONData, 'JSON Data')
    ]
    for model_item in model_list:
        if len(model_item) == 2:
            app_admin.add_view(ModelView(model_item[0], session, name=model_item[1]))
        else:
            app_admin.add_view(ModelView(model_item[0], session))

    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """This is a management script for the wiki application."""
    pass


if __name__ == '__main__':
    cli()
