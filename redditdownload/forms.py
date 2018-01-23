"""Forms module."""
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Optional


class IndexForm(FlaskForm):
    """Form for index."""
    subreddit = StringField('subreddit', validators=[DataRequired()])
    sort_mode = StringField('sort mode', validators=[Optional])
    time_mode = StringField('time mode', validators=[Optional])
    per_page = IntegerField('per page', validators=[Optional], default=0)
    disable_cache = BooleanField(validators=[Optional()])
