"""(The Database) — Where you define what an "Announcement" or "Deadline" looks like in SQL."""

from app import db
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import json, os

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    reads = db.relationship('AnnouncementRead', backref='announcement', lazy=True, cascade="all, delete-orphan")
    hearts = db.relationship('AnnouncementHeart', backref='announcement', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Announcement('{self.title}', '{self.date_posted}')"

class AnnouncementRead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)

    # Enforce uniqueness at the database level
    __table_args__ = (db.UniqueConstraint('user_id', 'announcement_id', name='unique_user_announcement_read'),)

class AnnouncementHeart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
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

    # Enforce that a course can only have one summary per specific date
    __table_args__ = (db.UniqueConstraint('course_id', 'date_held', name='unique_course_date_summary'),)

    def __repr__(self):
        return f'<ClassSummary {self.content}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
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

    completions = db.relationship('DeadlineCompletion', backref='deadline', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Deadline {self.description}>'

class DeadlineCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    deadline_id = db.Column(db.Integer, db.ForeignKey('deadline.id'), nullable=False)
    date_completed = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Ensures a user can't complete the exact same deadline twice
    __table_args__ = (db.UniqueConstraint('user_id', 'deadline_id', name='unique_user_deadline'),)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(80), nullable=False, default='Pending')
    admin_reply = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.DateTime, default=lambda:datetime.now(timezone.utc))
    is_pinned = db.Column(db.Boolean, default=False, nullable=True)

class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    
    # Store the entire JSON object as a text string
    subscription_data = db.Column(db.Text, nullable=False)

    def get_subscription_dict(self):
        # Helper function to convert the text back to a dictionary when sending pushes
        return json.loads(self.subscription_data)

# Place this helper table right above your User model
user_tags = db.Table('user_tags',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50))

cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    bio = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    role = db.Column(db.String(20), default="Student", nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(255), nullable=True)
    
    # Store it as a string, but it will hold the long scrambled hash
    password_hash = db.Column(db.String(256), nullable=False)

    announcements = db.relationship('Announcement', backref='author', lazy=True, cascade="all, delete-orphan")
    tags = db.relationship('Tag', secondary=user_tags, backref=db.backref('users', lazy='dynamic'))

    feedbacks = db.relationship('Feedback', backref='user', lazy=True, cascade="all, delete-orphan")
    announcement_reads = db.relationship('AnnouncementRead', backref='user', lazy=True, cascade="all, delete-orphan")
    announcement_hearts = db.relationship('AnnouncementHeart', backref='user', lazy=True, cascade="all, delete-orphan")
    deadline_completions = db.relationship('DeadlineCompletion', backref='user', lazy=True, cascade="all, delete-orphan")
    push_subscriptions = db.relationship('PushSubscription', backref='user', lazy=True, cascade="all, delete-orphan")

    # Watermark timestamps for page-level tracking
    last_viewed_summaries = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_viewed_links = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_viewed_courses = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # --- HELPER METHODS --- 
    def set_password(self, password):
        """Scrambles the plain text password and saves the hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Takes a plain text password, hashes it, and compares it to the database."""
        return check_password_hash(self.password_hash, password)

    def __init__(self, **kwargs):
        # 1. Run the standard SQLAlchemy initialization
        super(User, self).__init__(**kwargs)
        
        # 2. If no profile image was provided, generate one!
        if not self.profile_image and self.name:
            # Format the name for a URL (e.g., "Juan Dela Cruz" -> "Juan+Dela+Cruz")
            formatted_name = self.name.replace(' ', '+')
            
            # Use UI Avatars to generate a random colored badge with their initials
            self.profile_image = f"https://ui-avatars.com/api/?name={formatted_name}&background=random&color=fff&bold=true"

    def __repr__(self):
        return f"User('{self.name}')"