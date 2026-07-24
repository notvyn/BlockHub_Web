from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from app import db
from app.forms import LoginForm, SignupForm
from app.models import User

from app.auth import auth

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Check if the user exists AND the passwords match using Werkzeug
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            # Optional: Add a flash message here for invalid credentials
            pass
            
    return render_template('login.html', form=form, is_auth=True)

@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.dashboard'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None:
            new_user = User(
                name=form.name.data,
                email=form.email.data,
                role=form.role.data
            )
            # Use the new helper method to hash the password securely
            new_user.set_password(form.password.data)

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            return redirect(url_for('main.dashboard'))
        
    return render_template('signup.html', form=form, is_auth=True)

@auth.route('/verify-email/<token>')
@login_required
def verify_email_update(token):
    serializer = URLSafeTimedSerializer(auth.config['SECRET_KEY'])
    
    try:
        # Decrypt the token. Max_age=1800 means it expires in 1800 seconds (30 mins).
        data = serializer.loads(token, salt='email-update-salt', max_age=1800)
        
        user_id = data.get('user_id')
        new_email = data.get('new_email')
        
        # Security check: Ensure the logged-in user matches the token
        if current_user.id != user_id:
            flash('Invalid or unauthorized token.', 'danger')
            return redirect(url_for('main.settings'))

        # SUCCESS! Update the database.
        current_user.email = new_email
        db.session.commit()
        
        flash('Your email has been successfully updated!', 'success')
        return redirect(url_for('main.profile'))
        
    except SignatureExpired:
        flash('The verification link has expired. Please request a new one.', 'danger')
        return redirect(url_for('main.profile'))
        
    except BadSignature:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('main.profile'))