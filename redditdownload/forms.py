"""Forms module."""
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Optional


class IndexForm(FlaskForm):
    """Form for index."""
    subreddit = StringField('subreddit', validators=[DataRequired()])
    sort_mode = StringField('sort_mode', validators=[Optional])
    disable_cache = BooleanField(validators=[Optional()])
