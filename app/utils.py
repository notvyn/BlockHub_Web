from pywebpush import webpush, WebPushException
from flask import url_for, current_app
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from wtforms.validators import ValidationError
from app import mail

import json
import os
import re

# Grab your keys from your environment variables
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY') 
VAPID_CLAIM_EMAIL = os.environ.get('VAPID_CLAIM_EMAIL') # e.g., "mailto:your@email.com"

def send_web_push(subscription_dict, notification_title, notification_body, target_url="/"):
    """
    Packages the data and sends it to the browser's Push Service.
    """
    try:
        webpush(
            subscription_info=subscription_dict,
            data=json.dumps({
                "title": notification_title, 
                "body": notification_body,
                "url": target_url
            }),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIM_EMAIL}
        )
        print("Push sent successfully!")
        return "success" # NEW: Explicitly return success!
        
    except WebPushException as ex:
        error_message = str(ex)
        print("Push failed!", repr(ex))
        
        # THE FIX: A bulletproof string-match looking for "410" or "unsubscribed"
        if "410" in error_message or "unsubscribed" in error_message:
            print("Subscription expired or revoked. Telling route to delete!")
            return "expired" 
            
        return "error"

def send_verification_email(user, new_email):
    # 1. Initialize the serializer with your app's secret key
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    # 2. Package the user's ID and the NEW email into a secure token
    # We salt it so it can only be used for email updates
    token = serializer.dumps({'user_id': user.id, 'new_email': new_email}, salt='email-update-salt')
    
    # 3. Create the unique verification link
    verify_url = url_for('verify_email_update', token=token, _external=True)
    
    # 4. Construct the email
    msg = Message('Confirm Your BlockHub Email Update',
                  sender='noreply@blockhub.com',
                  recipients=[new_email]) # Send it to the NEW email to prove they own it
                  
    msg.body = f'''Hello {user.name},

You requested to change your BlockHub email address.
To confirm and apply this change, please visit the following link:

{verify_url}

If you did not make this request, please ignore this email and your account will remain secure.
This link will expire in 30 minutes.
'''
    # 5. Send it!
    mail.send(msg)

def validate_school_email(form, field):
    """Ensures the user is signing up with a valid BatStateU email format."""
    # ^\d{2}   = Starts with exactly 2 digits
    # -        = A literal hyphen
    # \d{5}    = Exactly 5 digits
    pattern = r'^\d{2}-\d{5}@g\.batstate-u\.edu\.ph$'
    
    if not re.match(pattern, field.data):
        raise ValidationError('Must use a valid university format (e.g., 25-00000@g.batstate-u.edu.ph).')
    
def validate_password_strength(form, field):
    """Ensures the password meets strict security requirements."""
    # Pattern: Min 8 chars, 1 uppercase, 1 lowercase, 1 number
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
    
    if not re.match(pattern, field.data):
        raise ValidationError('Password must be at least 8 characters and include a lowercase letter, an uppercase letter, and a number.')
    
    