"""(The Database) — Where you define what an "Announcement" or "Deadline" looks like in SQL."""

from app import db
from flask_login import UserMixin
from datetime import datetime, timezone

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Announcement('{self.title}', '{self.date_posted}')"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    role = db.Column(db.String(20), default="student", nullable=False)
    
    password_hash = db.Column(db.String(200), nullable=False)

    announcements = db.relationship('Announcement', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}')"
