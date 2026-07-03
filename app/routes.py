"""(Page Manager) - This is where the magic happens. It connects the URL (e.g., /dashboard) to the right HTML page."""

from flask import render_template, redirect, url_for

from app import app

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')