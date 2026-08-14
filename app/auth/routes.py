from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from app import db
from app.forms import LoginForm, SignupForm
from app.models import User
from app.utils import decode_token, send_verification_email

from app.auth import auth

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            
            # --- GUARDRAIL WITH RESEND LINK ---
            if not user.is_verified:
                # Generate a link pointing to our new route, passing their email
                resend_url = url_for('auth.resend_verification', email=user.email)
                
                # Inject the link directly into the flash message
                flash(f'Please verify your email address before logging in. Don\'t forget to check your spam folder! <br><a href="{resend_url}" class="alert-link text-decoration-underline"><i class="fa-solid fa-envelope me-1"></i> Click here to resend the email.</a>', 'warning')
                
                return redirect(url_for('auth.login'))
                
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('login.html', form=form, is_auth=True)

@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.dashboard'))

@auth.route('/resend-verification/<email>')
def resend_verification(email):
    # Find the user by the email passed in the URL
    user = User.query.filter_by(email=email).first()
    
    # Security checks
    if not user:
        flash('Account not found.', 'danger')
        return redirect(url_for('auth.signup'))
        
    if user.is_verified:
        flash('Your account is already verified! You can log in directly.', 'info')
        return redirect(url_for('auth.login'))
        
    try:
        # Fire the email function again
        send_verification_email(user, user.email)
        flash('A new verification email has been sent to your inbox. It will expire in 30 minutes.', 'success')
    except Exception as e:
        print(f"Resend Mail Error: {e}")
        flash('Failed to send the email. Please try again later.', 'danger')
        
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # If the user already exists, stop them immediately
        if user:
            flash('An account with this email already exists.', 'warning')
            return redirect(url_for('auth.signup'))

        # Create the new user
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data,
            is_verified=False
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        try:
            # Attempt to send the email
            send_verification_email(new_user, new_user.email)
            flash('Account created! Please check your university email (and spam folder) to verify your account.', 'info')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            # ROLLBACK: If the email fails, delete the user so they can try again later
            db.session.delete(new_user)
            db.session.commit()
            print(f"Mail Error: {e}")
            flash('There was an issue sending the verification email. Please try again later.', 'danger')
            return redirect(url_for('auth.signup'))

    return render_template('signup.html', form=form, is_auth=True)

@auth.route('/verify/<token>')
def verify_email(token):
    # Decode using the specific sign-up salt
    data = decode_token(token, salt='account-verify-salt')
    
    if not data:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))
        
    user = User.query.get(data['user_id'])
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    if user.is_verified:
        flash('Account already verified. Please log in.', 'info')
    else:
        # Flip the switch
        user.is_verified = True
        db.session.commit()
        flash('You have successfully verified your account! You may now log in.', 'success')
        
    return redirect(url_for('auth.login'))

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