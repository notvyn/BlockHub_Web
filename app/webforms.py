from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField, IntegerField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.widgets import TextArea
from datetime import date, timedelta

class AnnouncementForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = StringField("Content", widget=TextArea())
    url = StringField("URL", widget=TextArea())
    submit = SubmitField()

class ClassSummaryForm(FlaskForm):
    course = SelectField("Course", validators=[DataRequired()], coerce=int)
    content = StringField("Content", validators=[DataRequired()], widget=TextArea())
    scheduled_date = DateField("Scheduled Date",  default=date.today, validators=[DataRequired()])
    note = StringField("Note", widget=TextArea())
    submit = SubmitField()

class CourseForm(FlaskForm):
    code = StringField("Course Code", validators=[DataRequired()])
    title = StringField("Course Title", validators=[DataRequired()])
    instructor = StringField("Course Instructor", validators=[DataRequired()])
    units = IntegerField("Course Units", validators=[DataRequired()])
    submit = SubmitField()

def get_tomorrow():
    return date.today() + timedelta(days=1)

class DeadlineForm(FlaskForm):
    course = SelectField("Subject", validators=[DataRequired()], coerce=int)
    description = StringField("Task Description", validators=[DataRequired()])
    category = SelectField("Category", validators=[DataRequired()], choices=['Activity', 'Assignment', 'Quiz', 'Exam', 'Project', 'Laboratory', 'Recitation', 'Research', 'Group Activity', 'Presentation', 'Practical Test', 'Requirements'])

    date_given = DateField("Date Given", default=date.today, validators=[DataRequired()])
    due_date = DateField("Deadline", default=get_tomorrow, validators=[DataRequired()])

    status = SelectField("Status", default="Upcoming", validators=[DataRequired()], choices=['Upcoming', 'Pending', 'Done', 'Dropped'])

    note = StringField("Notes", widget=TextArea())
    submit = SubmitField()

class LinkForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    url = StringField("URL", validators=[DataRequired()], widget=TextArea())
    submit = SubmitField()

class LoginForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired()])
    submit = SubmitField()

class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), EqualTo('confirm_password', message='Password must Match!')])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    role = SelectField("Role", choices=[("", "Select your Role"), ("student", "Student"), ("officer", "Officer")], validators=[DataRequired()])
    submit = SubmitField()