from pywebpush import webpush, WebPushException
from flask import url_for, current_app
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from wtforms.validators import ValidationError
from app import mail

import json
import os
import re
import pdfplumber
import uuid
from datetime import datetime

# Grab the keys from the environment variables
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY') 
VAPID_CLAIM_EMAIL = os.environ.get('VAPID_CLAIM_EMAIL') # e.g., "mailto:your@email.com"

def extract_schedule_from_pdf(file_stream):
    """
    Reads the messy schedule PDF and returns a clean dictionary grouped by Day.
    """
    parsed_data = {
        'Monday': [], 'Tuesday': [], 'Wednesday': [], 
        'Thursday': [], 'Friday': [], 'Saturday': [], 'Sunday': []
    }
    
    previous_subjects = [""] * 7
    previous_rooms = [""] * 7

    with pdfplumber.open(file_stream) as pdf:
        first_page = pdf.pages[0]
        table = first_page.extract_table()
        
        if not table:
            raise ValueError("Could not find a table in this PDF.")

        for row in table[2:]: 
            time_block = row[0]
            if not time_block: 
                continue 

            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            col_index = 1
            
            for i, day in enumerate(days):
                if col_index + 1 < len(row):
                    subject = row[col_index]
                    room = row[col_index + 1]

                    if subject and str(subject).strip() != "":
                        if "-do-" in str(subject).lower():
                            subject = previous_subjects[i]
                        else:
                            previous_subjects[i] = str(subject).strip()

                        if room and "-do-" in str(room).lower():
                            room = previous_rooms[i]
                        else:
                            previous_rooms[i] = str(room).strip()

                        time_str = str(time_block).strip().replace('\n', '')
                        time_parts = time_str.split('-')
                        start_time = time_parts[0].strip()
                        end_time = time_parts[1].strip() if len(time_parts) > 1 else start_time

                        day_list = parsed_data[day]
                        
                        # Merge logic for consecutive identical classes
                        if day_list and day_list[-1]['course'] == subject and day_list[-1]['room'] == room:
                            prev_start = day_list[-1]['time'].split('-')[0].strip()
                            day_list[-1]['time'] = f"{prev_start} - {end_time}"
                        else:
                            day_list.append({
                                'id': uuid.uuid4().hex[:8],
                                'time': f"{start_time} - {end_time}",
                                'course': subject,
                                'room': room,
                                'day': day
                            })
                col_index += 2

    return parsed_data

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
        return "success" # Explicitly return success
        
    except WebPushException as ex:
        error_message = str(ex)
        print("Push failed!", repr(ex))
        
        # A string-match looking for "410" or "unsubscribed"
        if "410" in error_message or "unsubscribed" in error_message:
            print("Subscription expired or revoked. Telling route to delete!")
            return "expired" 
            
        return "error"

def send_verification_email(user, new_email):
    # Initialize the serializer with your app's secret key
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    # Package the user's ID and the NEW email into a secure token
    # We salt it so it can only be used for email updates
    token = serializer.dumps({'user_id': user.id, 'new_email': new_email}, salt='email-update-salt')
    
    # Create the unique verification link
    verify_url = url_for('verify_email_update', token=token, _external=True)
    
    # Construct the email
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
    # Send it!
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
    
    