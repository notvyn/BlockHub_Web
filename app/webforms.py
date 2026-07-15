from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, IntegerField, URLField, RadioField, TimeField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, URL, Optional
from wtforms.widgets import TextArea
from datetime import date, timedelta, time

class AnnouncementForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = StringField("Content", widget=TextArea())
    url = StringField("URL", validators=[Optional()], widget=TextArea())
    submit = SubmitField()

class ClassSummaryForm(FlaskForm):
    course = RadioField("Course", validators=[DataRequired()], coerce=int)
    schedule = RadioField("Select Schedule", validators=[DataRequired()], coerce=int)
    content = StringField("Content", validators=[DataRequired()], widget=TextArea())
    date_held = DateField("Date Held",  default=date.today, validators=[DataRequired()])
    note = StringField("Note", widget=TextArea())
    submit = SubmitField()

class CourseForm(FlaskForm):
    code = StringField("Course Code", validators=[DataRequired()])
    title = StringField("Course Title", validators=[DataRequired()])
    instructor = StringField("Course Instructor", validators=[DataRequired()])
    instructor_email = StringField("Instructor Email", validators=[Optional(), Email()])
    units = FloatField("Course Units", validators=[DataRequired()])
    submit = SubmitField()

class CourseScheduleForm(FlaskForm):
    day = RadioField("Day", validators=[DataRequired()], choices=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    start_time = TimeField("Start Time", default=time, validators=[DataRequired()])
    end_time = TimeField("End Time", default=time, validators=[DataRequired()])
    room = StringField("Room", validators=[DataRequired()])
    submit = SubmitField()

def get_tomorrow():
    return date.today() + timedelta(days=1)

class DeadlineForm(FlaskForm):
    course = RadioField("Subject", validators=[DataRequired()], coerce=int)
    description = StringField("Task Description", validators=[DataRequired()])
    category = RadioField("Category", validators=[DataRequired()], choices=['Activity', 'Assignment', 'Quiz', 'Exam', 'Project', 'Laboratory', 'Recitation', 'Research', 'Group Activity', 'Presentation', 'Practical Test', 'Requirements'])

    date_given = DateField("Date Given", default=date.today, validators=[DataRequired()])
    due_date = DateField("Deadline", default=get_tomorrow, validators=[DataRequired()])

    status = RadioField("Status", default="Upcoming", validators=[DataRequired()], choices=['Upcoming', 'Pending', 'Done', 'Dropped'])

    note = StringField("Notes", widget=TextArea())
    submit = SubmitField()

class LinkForm(FlaskForm):
    title = StringField("Link Title", validators=[DataRequired()])
    url = URLField("URL", validators=[DataRequired(), URL()], widget=TextArea())
    submit = SubmitField('Save Link')

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