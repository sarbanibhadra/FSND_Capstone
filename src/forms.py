from datetime import datetime
from flask_wtf import Form
from wtforms import StringField, DateTimeField
from wtforms.validators import DataRequired

class ActorForm(Form):
    name = StringField(
        'name'
    )
    age = StringField(
        'age'
    )
    gender = StringField(
        'gender'
    )

class MovieForm(Form):
    title = StringField(
        'title', validators=[DataRequired()]
    )

    release_date = DateTimeField(
        'release_date',
        validators=[DataRequired()],
        default= datetime.today()
    )

    actors = StringField(
        'actors'
    )