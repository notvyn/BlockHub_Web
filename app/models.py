"""(The Database) — Where you define what an "Announcement" or "Deadline" looks like in SQL."""

from app import db
from flask_login import UserMixin
from datetime import datetime, timezone

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

    content = db.Column(db.Text, nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
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

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    role = db.Column(db.String(20), default="student", nullable=False)
    
    password_hash = db.Column(db.String(200), nullable=False)

    announcements = db.relationship('Announcement', backref='author', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"User('{self.name}')"
