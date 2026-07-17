"""(The Database) — Where you define what an "Announcement" or "Deadline" looks like in SQL."""

from app import db
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import json

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Announcement('{self.title}', '{self.date_posted}')"

class AnnouncementRead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)

class AnnouncementHeart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # The user who clicked the heart
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # The announcement they hearted
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    
    # Optional: Track when they liked it
    date_hearted = db.Column(db.DateTime, default=datetime.utcnow)

class ClassSummary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('course_schedule.id'), nullable=True)

    schedule = db.relationship('CourseSchedule', backref='summaries', lazy=True)

    content = db.Column(db.Text, nullable=False)
    date_held = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, default=lambda:datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ClassSummary {self.content}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    instructor = db.Column(db.String(200), nullable=False)
    instructor_email = db.Column(db.String(200), nullable=True)
    units = db.Column(db.Numeric(precision=3, scale=2), nullable=False)
    date_added = db.Column(db.DateTime, default=lambda:datetime.now(timezone.utc))

    deadline = db.relationship('Deadline', backref='course', lazy=True, cascade="all, delete-orphan")
    class_summary = db.relationship('ClassSummary', backref='course', lazy=True, cascade="all, delete-orphan")
    schedules = db.relationship('CourseSchedule', backref='course', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Course {self.code}>'

class CourseSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    day = db.Column(db.String(50), nullable=False)
    
    # CHANGED: These must be db.Time to accept WTForms TimeField data
    start_time = db.Column(db.Time, nullable=False) 
    end_time = db.Column(db.Time, nullable=False)

    room = db.Column(db.String(50), nullable=False, server_default='TBA')
    
    date_added = db.Column(db.DateTime, default=lambda:datetime.now(timezone.utc))

class Deadline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date_given = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Upcoming')
    note = db.Column(db.Text, nullable=True)

    date_added = db.Column(db.DateTime, default=lambda:datetime.now(timezone.utc))
    is_archived = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Deadline {self.description}>'

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=lambda:datetime.now(timezone.utc))

# Place this helper table right above your User model
user_tags = db.Table('user_tags',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50)) # e.g., "Technical", "Interest", "Role"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    bio = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    role = db.Column(db.String(20), default="Student", nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(255), nullable=True, default='https://res.cloudinary.com/your-cloud-name/image/upload/v12345/default-avatar.png')
    
    # We still store it as a string, but it will hold the long scrambled hash
    password_hash = db.Column(db.String(256), nullable=False)

    announcements = db.relationship('Announcement', backref='author', lazy=True, cascade="all, delete-orphan")
    tags = db.relationship('Tag', secondary=user_tags, backref=db.backref('users', lazy='dynamic'))

    # --- NEW HELPER METHODS ---
    def set_password(self, password):
        """Scrambles the plain text password and saves the hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Takes a plain text password, hashes it, and compares it to the database."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.name}')"

class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Change 'user.id' if your user table is named differently!
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    
    # We will store the entire JSON object as a text string
    subscription_data = db.Column(db.Text, nullable=False)

    def get_subscription_dict(self):
        # Helper function to convert the text back to a dictionary when sending pushes
        return json.loads(self.subscription_data)
    
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(80), nullable=False, default='Pending')
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))