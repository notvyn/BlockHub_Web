"""(Page Manager) - This is where the magic happens. It connects the URL (e.g., /dashboard) to the right HTML page."""

from flask import render_template, redirect, url_for

from app import app, login_manager
from app.models import User
from app.webforms import DeadlineForm

@login_manager.user_loader
def load_user(user_id):
    # This looks up the user in your database by their ID
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/dashboard')
def dashboard():
    deadline_form = DeadlineForm()
    
    # deadlines = Deadline.

    return render_template('dashboard.html')