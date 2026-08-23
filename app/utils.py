from pywebpush import webpush, WebPushException
from flask import url_for, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
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

def send_verification_email(user, target_email, action='verify_account'):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    # SET THE PROFESSIONAL SENDER NAME
    sender_info = ('BlockHub Admin', 'blockhub.komsy3@gmail.com')

    if action == 'update_email':
        token = serializer.dumps({'user_id': user.id, 'new_email': target_email}, salt='email-update-salt')
        verify_url = url_for('auth.verify_email_update', token=token, _external=True) 
        
        subject = 'Confirm Your BlockHub Email Update'
        
        # CREATE A STYLED HTML BODY
        html_body = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 30px; border: 1px solid #eaeaea; border-radius: 12px; background-color: #ffffff;">
            <h2 style="color: #6c5ce7; text-align: center; margin-bottom: 20px;">Email Update Request</h2>
            <p style="color: #333; font-size: 16px;">Hello <strong>{user.name}</strong>,</p>
            <p style="color: #555; font-size: 15px; line-height: 1.5;">You requested to change your BlockHub email address. To confirm and apply this change, please click the button below:</p>
            
            <div style="text-align: center; margin: 35px 0;">
                <a href="{verify_url}" style="background-color: #6c5ce7; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">Confirm Email Update</a>
            </div>
            
            <p style="font-size: 12px; color: #999; text-align: center; margin-top: 30px border-top: 1px solid #eaeaea; padding-top: 20px;">
                If you did not make this request, please ignore this email. Your account remains secure.<br>This link will expire in 30 minutes.
            </p>
        </div>
        """
        
        # Fallback text for email clients that block HTML
        fallback_body = f"Hello {user.name},\n\nConfirm your email update here: {verify_url}"

    elif action == 'reset_password':
        token = serializer.dumps({'user_id': user.id}, salt='password-reset-salt')
        verify_url = url_for('auth.reset_token', token=token, _external=True) 
        
        subject = 'Reset Your BlockHub Password'
        
        html_body = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 30px; border: 1px solid #eaeaea; border-radius: 12px; background-color: #ffffff;">
            <h2 style="color: #6c5ce7; text-align: center; margin-bottom: 20px;">Password Reset Request</h2>
            <p style="color: #333; font-size: 16px;">Hello <strong>{user.name}</strong>,</p>
            <p style="color: #555; font-size: 15px; line-height: 1.5;">We received a request to reset your BlockHub password. Click the button below to choose a new one:</p>
            
            <div style="text-align: center; margin: 35px 0;">
                <a href="{verify_url}" style="background-color: #6c5ce7; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">Reset Password</a>
            </div>
            
            <p style="font-size: 12px; color: #999; text-align: center; margin-top: 30px border-top: 1px solid #eaeaea; padding-top: 20px;">
                If you did not make this request, please ignore this email. Your password will remain unchanged.<br>This link will expire in 30 minutes.
            </p>
        </div>
        """
        fallback_body = f"Hello {user.name},\n\nReset your password here: {verify_url}"

    else:
        token = serializer.dumps({'user_id': user.id}, salt='account-verify-salt')
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        
        subject = 'Welcome to BlockHub! Verify Your Account'
        
        # HTML for New Account Sign-Up
        html_body = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 30px; border: 1px solid #eaeaea; border-radius: 12px; background-color: #ffffff;">
            <h2 style="color: #6c5ce7; text-align: center; margin-bottom: 20px;">Welcome to BlockHub!</h2>
            <p style="color: #333; font-size: 16px;">Hello <strong>{user.name}</strong>,</p>
            <p style="color: #555; font-size: 15px; line-height: 1.5;">We are excited to have you on board! To fully activate your account and access the dashboard, please verify your university email address by clicking the button below:</p>
            
            <div style="text-align: center; margin: 35px 0;">
                <a href="{verify_url}" style="background-color: #6c5ce7; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">Verify My Account</a>
            </div>
            
            <p style="font-size: 12px; color: #999; text-align: center; margin-top: 30px; border-top: 1px solid #eaeaea; padding-top: 20px;">
                If the button above does not work, copy and paste this link into your browser:<br>
                <span style="color: #6c5ce7;">{verify_url}</span><br><br>
                This link will expire in 30 minutes.
            </p>
        </div>
        """
        
        fallback_body = f"Hello {user.name},\n\nWelcome to BlockHub! Verify your account here: {verify_url}"

    # ASSEMBLE AND SEND
    # Notice we pass the sender_info tuple here
    msg = Message(subject, sender=sender_info, recipients=[target_email])
    
    # Attach both the beautiful HTML and the raw text fallback
    msg.html = html_body
    msg.body = fallback_body 
    
    mail.send(msg)

def decode_token(token, salt, expiration=1800):
    """
    Securely decodes a token. Returns the data if valid, or None if expired/tampered.
    expiration=1800 means 30 minutes.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(token, salt=salt, max_age=expiration)
        return data
    except (SignatureExpired, BadTimeSignature):
        return None

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
    
    