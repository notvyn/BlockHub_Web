from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField, IntegerField, TimeField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea
from datetime import date


class DeadlineForm(FlaskForm):
    course = SelectField("Subject", validators=[DataRequired()], coerce=int)
    description = StringField("Task Description", validators=[DataRequired()])
    category = SelectField("Category", validators=[DataRequired()], choices=[])

    date_given = DateField("Date Given", default=date.today, validators=[DataRequired()])
    due_date = DateField("Deadline", validators=[DataRequired()])

    status = SelectField("Status", default="Upcoming", validators=[DataRequired()], choices=['Upcoming', 'Pending', 'Done', 'Dropped'])

    note = StringField("Notes", widget=TextArea())