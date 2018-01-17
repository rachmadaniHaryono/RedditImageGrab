#!/usr/bin/python3
from flask import Flask
from flask.cli import FlaskGroup
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(script_info=None):
    app = Flask(__name__)
    db.init_app(app)

    @app.shell_context_processor
    def shell_context():
        return {'app': app, 'db': db}

    return app


cli = FlaskGroup(create_app=create_app)


@cli.command
def custom_command():
    pass


if __name__ == '__main__':
    cli()
