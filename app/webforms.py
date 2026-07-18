from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, IntegerField, URLField, RadioField, TimeField, FloatField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Email, EqualTo, URL, Optional, Length
from wtforms.widgets import TextArea
from flask_wtf.file import FileField, FileAllowed
from datetime import date, timedelta, time

from app.utility import validate_school_email, validate_password_strength

class AnnouncementForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = StringField("Content", validators=[DataRequired()], widget=TextArea())
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
    name = StringField("Name", validators=[DataRequired(), Length(min=8, max=120, message="Name must be between 8 and 120 characters.")])
    email = StringField("Email", validators=[DataRequired(), validate_school_email])
    password = PasswordField("Password", validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    role = RadioField("Role", choices=[("Student", "Student"), ("Officer", "Officer")], default="Student", validators=[DataRequired()])
    submit = SubmitField('Create Account')

class FeedbackForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    category = RadioField("Category", validators=[DataRequired()], choices=['Bug', 'Suggestion', 'Question', 'Other'])
    message = StringField("Message", validators=[DataRequired()], widget=TextArea())
    submit = SubmitField()

class ProfileForm(FlaskForm):
    # Standard text inputs
    name = StringField('Display Name', validators=[DataRequired()])
    # email = StringField('Email Address', validators=[DataRequired(), Email()])
    bio = StringField('Profile Bio', widget=TextArea())
    
    # The image upload field with a security check to only allow images
    profile_pic = FileField('Update Profile Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only please!')
    ])

    tags = SelectMultipleField('Profile Tags', coerce=int, widget=widgets.ListWidget(prefix_label=False), option_widget=widgets.CheckboxInput())
    
    submit = SubmitField('Save Changes')

class CreateTagForm(FlaskForm):
    tag_name = StringField('Tag Name', validators=[DataRequired()])
    tag_category = SelectField('Category', choices=[('Technical', 'Technical'), ('Interest', 'Interest'), ('Role', 'Role')])
    submit = SubmitField('Create Tag')