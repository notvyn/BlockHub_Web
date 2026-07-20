"""(Page Manager) - This is where the magic happens. It connects the URL (e.g., /dashboard) to the right HTML page."""

from flask import render_template, redirect, url_for, request, jsonify, send_from_directory, flash
from flask_login import current_user, login_user, login_required, logout_user
from sqlalchemy import func, and_, or_, text
from sqlalchemy.orm import joinedload
from datetime import date, timedelta, datetime, timezone, time
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict

from app import app, login_manager, db

import cloudinary
import cloudinary.uploader
import os
import json

from app.models import User, Announcement, AnnouncementRead, AnnouncementHeart, ClassSummary, Course, CourseSchedule, Deadline, Link, PushSubscription, Feedback, Tag, DeadlineCompletion
from app.webforms import AnnouncementForm, ClassSummaryForm, CourseForm, CourseScheduleForm, DeadlineForm, LinkForm, LoginForm, SignupForm, FeedbackForm, ProfileForm, CreateTagForm
from app.filter import markdown_filter, parse_links_filter, extract_images_filter, remove_images_filter, time_ago_filter
from app.utility import send_web_push, send_verification_email

@login_manager.user_loader
def load_user(user_id):
    # This looks up the user in your database by their ID
    return User.query.get(int(user_id))

# Put this alongside your other routes!
@app.route('/sw.js')
def serve_sw():
    # This tells Flask to serve the file from the static folder, 
    # but the browser will think it's at the root (http://localhost:5000/sw.js)
    return send_from_directory('static', 'js/sw.js', mimetype='application/javascript')

@app.route('/api/save-subscription', methods=['POST'])
@login_required # Ensures we know exactly who is saving this subscription
def save_subscription():
    sub_data = request.json
    
    if not sub_data:
        return jsonify({'error': 'No subscription data provided'}), 400

    # Convert the JSON dictionary back to a string so we can save it in the Text column
    sub_string = json.dumps(sub_data)

    # Check if this exact subscription already exists so we don't save duplicates
    existing_sub = PushSubscription.query.filter_by(
        user_id=current_user.id, 
        subscription_data=sub_string
    ).first()

    if not existing_sub:
        new_sub = PushSubscription(
            user_id=current_user.id,
            subscription_data=sub_string
        )
        db.session.add(new_sub)
        db.session.commit()

    return jsonify({'status': 'success', 'message': 'Subscription saved!'}), 200

@app.context_processor
def inject_global_forms():
    """
    This makes the LinkForm available to every single HTML template automatically,
    so our global modal.html never crashes.
    """
    return dict(link_form=LinkForm())

@app.route('/api/search')
# @login_required # Keeps search data private to logged-in users
def global_search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'results': []})
        
    search_term = f"%{query}%"
    results = []

    # 1. Search Links
    links = Link.query.filter(Link.title.ilike(search_term)).limit(3).all()
    for link in links:
        results.append({'type': 'Link', 'title': link.title, 'url': f"{url_for('links')}#link-{link.id}", 'icon': 'fa-link'})

    # 2. Search Announcements
    announcements = Announcement.query.filter(
        or_(Announcement.title.ilike(search_term), Announcement.content.ilike(search_term))
    ).limit(3).all()
    for a in announcements:
        results.append({'type': 'Announcement', 'title': a.title, 'url': url_for('announcement', id=a.id), 'icon': 'fa-bullhorn'})

    # 3. Search Deadlines
    deadlines = Deadline.query.filter(Deadline.description.ilike(search_term)).limit(3).all()
    for d in deadlines:
        results.append({'type': 'Deadline', 'title': d.description, 'url': f"{url_for('deadlines')}#deadline-{d.id}", 'icon': 'fa-clock'})

    # 4. Search Class Summaries
    summaries = ClassSummary.query.filter(ClassSummary.content.ilike(search_term)).limit(3).all()
    for s in summaries:
        results.append({'type': 'Summary', 'title': f"{s.course.code} Summary", 'url': url_for('summary', id=s.id), 'icon': 'fa-book-open'})

    courses = Course.query.filter(
        or_(Course.code.ilike(search_term), Course.title.ilike(search_term), or_(Course.instructor.ilike(search_term)))
    ).limit(3).all()
    for c in courses:
        results.append({'type': 'Course', 'title': f"{c.code} | {c.title}", 'url': f"{url_for('courses')}#course-{c.id}", 'icon': 'fa-address-book'})

    return jsonify({'results': results})

@app.route('/complete-deadline/<int:id>', methods=['POST'])
@login_required
def complete_deadline(id):
    data = request.get_json()
    is_completed = data.get('completed', False)

    # 1. Check if a completion record already exists for THIS user and THIS deadline
    completion = DeadlineCompletion.query.filter_by(user_id=current_user.id, deadline_id=id).first()

    # 2. Add or Remove the record based on the checkbox state
    if is_completed and not completion:
        # Checkbox was checked (true), and no record exists -> CREATE IT
        new_completion = DeadlineCompletion(user_id=current_user.id, deadline_id=id)
        db.session.add(new_completion)
        
    elif not is_completed and completion:
        # Checkbox was unchecked (false), and a record exists -> DELETE IT
        db.session.delete(completion)
    
    # Save the changes to the database
    db.session.commit()

    # 3. Calculate the new badge totals dynamically for the JS to update the UI
    # Total deadlines completed by this specific user
    archive_total = DeadlineCompletion.query.filter_by(user_id=current_user.id).count()
    
    # Total active deadlines (Total global deadlines MINUS what the user has completed)
    total_global_deadlines = Deadline.query.count()
    new_total = total_global_deadlines - archive_total

    # Send the success response back to the Javascript fetch call
    return jsonify({
        'success': True,
        'new_total': new_total,
        'archive_total': archive_total
    })

@app.route('/complete-feedback/<int:id>', methods=['POST'])
def complete_feedback(id):
    data = request.get_json()
    is_completed = data.get('completed', False)
    
    feedback = Feedback.query.get_or_404(id)
    
    # Update the status based on the checkbox
    if is_completed:
        feedback.status = 'Resolved'
    else:
        feedback.status = 'Pending'
        
    db.session.commit()

    # Send BOTH totals back to the JavaScript
    return jsonify({    
        'success': True
    })

@app.route('/mark-announcement-read/<int:id>', methods=['POST'])
@login_required
def mark_read(id):
    # Check if a receipt already exists so we don't make duplicates
    existing_receipt = AnnouncementRead.query.filter_by(
        user_id=current_user.id, 
        announcement_id=id
    ).first()
    
    # If not, create one!
    if not existing_receipt:
        receipt = AnnouncementRead(user_id=current_user.id, announcement_id=id)
        db.session.add(receipt)
        db.session.commit()
        
    return {"status": "success"} # We just return a tiny dictionary, no HTML template!

@app.route('/sync-guest-reads', methods=['POST'])
@login_required
def sync_guest_reads():
    # 1. Catch the JSON data sent by JavaScript
    data = request.get_json()
    
    # 2. Extract the list of IDs (or default to an empty list)
    announcement_ids = data.get('ids', [])
    
    # 3. Loop through the IDs and save them to the database
    for a_id in announcement_ids:
        # Check if the receipt already exists so we don't cause a database error
        existing = AnnouncementRead.query.filter_by(
            user_id=current_user.id, 
            announcement_id=a_id
        ).first()
        
        if not existing:
            receipt = AnnouncementRead(user_id=current_user.id, announcement_id=a_id)
            db.session.add(receipt)
            
    # 4. Commit all the new receipts at once
    db.session.commit()
    
    return jsonify({"status": "success"})

@app.route('/toggle-heart/<int:announcement_id>', methods=['POST'])
def toggle_heart(announcement_id):
    # Check if the user already hearted this announcement
    existing_heart = AnnouncementHeart.query.filter_by(
        user_id=current_user.id, 
        announcement_id=announcement_id
    ).first()

    if existing_heart:
        # If it exists, they are "un-hearting" it
        db.session.delete(existing_heart)
        is_hearted = False
    else:
        # If it doesn't exist, they are "hearting" it
        new_heart = AnnouncementHeart(user_id=current_user.id, announcement_id=announcement_id)
        db.session.add(new_heart)
        is_hearted = True
        
    db.session.commit()

    # Count the new total of hearts for this announcement
    total_hearts = AnnouncementHeart.query.filter_by(announcement_id=announcement_id).count()

    # Send the data back to the JavaScript
    return jsonify({'success': True, 'is_hearted': is_hearted, 'total_hearts': total_hearts})

@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    
    try:
        # NEW: Tell Cloudinary to auto-detect if it's an image, video, or raw file (like a PDF)
        upload_result = cloudinary.uploader.upload(file, resource_type='auto')
        
        image_url = upload_result.get("secure_url")
        
        return jsonify({'data': {'filePath': image_url}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/', methods=['GET', 'POST'])
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    announcement_form = AnnouncementForm()
    class_summary_form = DeadlineForm()
    deadline_form = DeadlineForm()
    
    # ---------------------------------------------------------
    # 1. TOTAL COUNTS (The highly optimized database way)
    # ---------------------------------------------------------
    total_announcements = Announcement.query.count()
    
    # total_deadlines = Deadline.query.filter(
    #     Deadline.status.in_(['Upcoming', 'Pending'])
    # ).count()

    # ---------------------------------------------------------
    # 2. THE HYBRID ANNOUNCEMENT LOGIC
    # ---------------------------------------------------------
    read_announcement_ids = []
    final_announcements = []

    if current_user.is_authenticated:
        user = User.query.get(current_user.id)
        
        # Get IDs of what this user has read
        read_records = AnnouncementRead.query.filter_by(user_id=current_user.id).all()
        read_announcement_ids = [record.announcement_id for record in read_records]

        # Fetch ALL unread announcements for this user
        unread_announcements = Announcement.query.filter(
            ~Announcement.id.in_(read_announcement_ids)
        ).all()

        # Fetch the absolute latest 3 announcements (for dashboard context)
        latest_announcements = Announcement.query.order_by(
            Announcement.date_posted.desc()
        ).limit(3).all()

        # Merge them using a dictionary to automatically remove duplicates
        merged_dict = {a.id: a for a in unread_announcements}
        for a in latest_announcements:
            if a.id not in merged_dict:
                merged_dict[a.id] = a

        # Sort the final merged list by date (newest at the top)
        final_announcements = sorted(merged_dict.values(), key=lambda x: x.date_posted, reverse=True)
    else:
        user = None
        # Fallback for logged-out users
        final_announcements = Announcement.query.order_by(Announcement.date_posted.desc()).limit(3).all()

    # announcement = Announcement.query.order_by(Announcement.date_posted.desc()).limit(3).all()

    # # THE FIX: Only check read receipts if they are actually logged in
    # read_announcement_ids = []
    # if current_user.is_authenticated:
    #     # Get a list of announcement IDs that THIS user has explicitly read
    #     read_records = AnnouncementRead.query.filter_by(user_id=current_user.id).all()
    #     read_announcement_ids = [record.announcement_id for record in read_records]

    # upcoming_deadline = Deadline.query.filter(Deadline.status.in_(['Upcoming', 'Pending'])).all()
    # total_deadline = len(upcoming_deadline)

    # deadline = Deadline.query.filter(Deadline.status.in_(['Upcoming', 'Pending'])).order_by(Deadline.due_date).limit(3).all()
    
    # class_summary = ClassSummary.query.order_by(ClassSummary.date_held).all()

    # link = Link.query.order_by(Link.date_added).all()

    # ---------------------------------------------------------
    # 3. DEADLINES & OTHER DATA
    # ---------------------------------------------------------

    # 1. Grab the exact UTC time, remove timezone info, and add 8 hours for PHT
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    ph_time = now_utc + timedelta(hours=8)
    
    # 2. Calculate the 24-hour grace period based on Philippine Time
    cutoff_time = ph_time - timedelta(days=1)

    completed_ids = []

    if current_user.is_authenticated:
    # 1. What has the user already checked off?
        completed_ids = [c.deadline_id for c in DeadlineCompletion.query.filter_by(user_id=current_user.id).all()]

    # 2. Start the query: Only get tasks where the deadline is STILL IN THE FUTURE (or grace period)
    active_query = Deadline.query.filter(Deadline.due_date >= cutoff_time)
    
    # 3. Filter out the ones they already clicked "Done" on
    if completed_ids:
        active_query = active_query.filter(Deadline.id.notin_(completed_ids))
        
    active_deadlines = active_query.order_by(Deadline.due_date.asc()).all()

    # --- NEW: Give the date a clock (11:59 PM) so Jinja can do exact hour math ---
    for d in active_deadlines:
        if type(d.due_date) is date:
            d.due_datetime = datetime.combine(d.due_date, time(23, 59, 59))
        else:
            d.due_datetime = d.due_date

    links = Link.query.order_by(Link.date_added).limit(3).all()

    # 1. Grab the exact UTC time, remove timezone info, and add 8 hours for PHT
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    ph_time = now_utc + timedelta(hours=8)
    
    # 2. Calculate the 24-hour grace period based on Philippine Time
    cutoff_time = ph_time - timedelta(days=1)

    # 1. Math: Sunday is 6. If today is Wed (2), 6 - 2 = 4 days until Sunday.
    days_until_sunday = 6 - ph_time.weekday()
    
    # 2. Add those days to today's date to find the exact date of this Sunday
    end_of_week = ph_time + timedelta(days=days_until_sunday)

    # 1. Grab the absolute newest record, regardless of time.
    target_record = ClassSummary.query.order_by(ClassSummary.date_held.desc()).first()
    
    # 2. Create an empty dictionary to hold our grouped data
    daily_summaries = {}
    
    if target_record:
        # 2. Extract just the calendar date from the newest record
        record_date = target_record.date_held
        if hasattr(record_date, 'date'):
            record_date = record_date.date()
            
        # 3. Calculate how many days old it is
        days_old = (ph_time - record_date).days
        
        # 4. If it is 3 days old or less, fetch all summaries for that calendar day
        if days_old <= 3:
            # 1. Fetch the raw summaries just like before
            raw_summaries = ClassSummary.query.options(joinedload(ClassSummary.course)).filter(
                func.date(ClassSummary.date_held) == record_date
            ).all()

            for summary in raw_summaries:
                course_header = f"{summary.course.code} | {summary.course.title}"
            
                # If we haven't seen this course yet, create a new list for it
                if course_header not in daily_summaries:
                    daily_summaries[course_header] = []
                    
                # Add the summary to that course's list
                daily_summaries[course_header].append(summary)
        else:
            # If it's too old, trigger the "No recent summaries" UI
            target_record = None

    # if current_user.is_authenticated:
    #     user = User.query.get(current_user.id)
    # else:
    #     user = None

    return render_template('dashboard.html',
        announcement_form=announcement_form,
        class_summary_form=class_summary_form,
        deadline_form=deadline_form,
        announcements=final_announcements,
        read_ids=read_announcement_ids,
        deadlines=active_deadlines,
        target_record=target_record,
        daily_summaries=daily_summaries,
        links=links,
        user=user,
        today=ph_time,
        end_of_week=end_of_week,
        completed_ids=completed_ids
    )

@app.route('/add-entry/announcement', methods=['GET', 'POST'])
@login_required
def add_announcement():
    form = AnnouncementForm()

    if form.validate_on_submit():
        new_announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            url=form.url.data,
            user_id=current_user.id
        )

        form.title.data = ''
        form.content.data = ''
        form.url.data = ''

        db.session.add(new_announcement)

        # Grab all saved browser subscriptions from the database
        all_subscriptions = PushSubscription.query.all()
        
        for sub in all_subscriptions:
            # Use the helper method we made in models.py to turn the text back into a dictionary
            sub_dict = sub.get_subscription_dict()
            
            # Fire the message!
            status = send_web_push(
                subscription_dict=sub_dict, 
                notification_title="New Class Announcement!", 
                notification_body=new_announcement.title,
                target_url=f"/announcements#announcement-{new_announcement.id}"
            )

            # NEW: Automatically clean the database if the address is dead!
            if status == "expired":
                db.session.delete(sub)

        db.session.commit()

        return redirect(url_for('announcements'))

    return render_template('add-announcement.html', form=form, has_back_btn=True, is_entry=True)

@app.route('/add-entry/course', methods=['GET', 'POST'])
def add_course():
    form = CourseForm()

    if form.validate_on_submit():
        new_course = Course(
            code=form.code.data,
            title=form.title.data,
            instructor=form.instructor.data,
            instructor_email=form.instructor_email.data,
            units=form.units.data,
        )

        form.code.data = ''
        form.title.data = ''
        form.instructor.data = ''
        form.instructor_email.data = ''
        form.units.data = ''

        db.session.add(new_course)
        db.session.commit()

        # Grab all saved browser subscriptions from the database
        all_subscriptions = PushSubscription.query.all()

        for sub in all_subscriptions:
            # Use the helper method we made in models.py to turn the text back into a dictionary
            sub_dict = sub.get_subscription_dict()
            
            # Fire the message!
            status = send_web_push(
                subscription_dict=sub_dict, 
                notification_title="New Class Course!", 
                notification_body=new_course.title,
                target_url=f"/courses#course-{new_course.id}"
            )

            # NEW: Automatically clean the database if the address is dead!
            if status == "expired":
                db.session.delete(sub)

        db.session.commit()

        # flash("Course Added Successfully")

        return redirect(url_for('courses'))
    
    return render_template('add-course.html', form=form, has_back_btn=True, is_entry=True)

@app.route('/add-entry/deadline', methods=['GET', 'POST'])
def add_deadline():
    form = DeadlineForm()

    course = Course.query.all()

    form.course.choices = [(c.id, f"{c.code} | {c.title}") for c in course]
    
    if form.validate_on_submit():
        new_deadline = Deadline(
            course_id=form.course.data,
            description=form.description.data,
            category=form.category.data,
            date_given=form.date_given.data,
            due_date=form.due_date.data,
            status=form.status.data,
            note=form.note.data
        )

        form.course.data = ''
        form.description.data = ''
        form.category.data = ''
        form.date_given.data = None
        form.due_date.data = None
        form.status.data = ''
        form.note.data = ''

        db.session.add(new_deadline)

        # Grab all saved browser subscriptions from the database
        all_subscriptions = PushSubscription.query.all()
        
        for sub in all_subscriptions:
            # Use the helper method we made in models.py to turn the text back into a dictionary
            sub_dict = sub.get_subscription_dict()
            
            # Fire the message!
            status = send_web_push(
                subscription_dict=sub_dict, 
                notification_title="New Class Deadline!", 
                notification_body=new_deadline.description,
                target_url=f"/deadlines#deadline-{new_deadline.id}"
            )

            # NEW: Automatically clean the database if the address is dead!
            if status == "expired":
                db.session.delete(sub)

        db.session.commit()

        # flash("Deadline Posted Successfully")

        return redirect(url_for('deadlines'))

    return render_template('add-deadline.html', form=form, has_back_btn=True, is_entry=True)

# @app.route('/add-entry/link', methods=['GET', 'POST'])
# def add_link():
#     form = LinkForm()

#     if form.validate_on_submit():
#         new_link = Link(
#             title=form.title.data,
#             url=form.url.data
#         )

#         form.title.data = ''
#         form.url.data = ''

#         db.session.add(new_link)
#         db.session.commit()

#         return redirect(url_for('add_link'))

#     return render_template('add-link.html', form=form)

@app.route('/api/add-link', methods=['POST'])
def add_link_api():
    form = LinkForm()
    
    # WTForms automatically checks the CSRF token and the URL format here!
    if form.validate_on_submit():
        new_link = Link(
            title=form.title.data, 
            url=form.url.data,
            # user_id=current_user.id  # If your links are tied to specific users
        )
        db.session.add(new_link)

        # Grab all saved browser subscriptions from the database
        all_subscriptions = PushSubscription.query.all()
        
        for sub in all_subscriptions:
            # Use the helper method we made in models.py to turn the text back into a dictionary
            sub_dict = sub.get_subscription_dict()
            
            # Fire the message!
            status = send_web_push(
                subscription_dict=sub_dict, 
                notification_title="New Class Link!", 
                notification_body=new_link.title,
                target_url=f"/links#link-{new_link.id}"
            )

            # NEW: Automatically clean the database if the address is dead!
            if status == "expired":
                db.session.delete(sub)

        db.session.commit()
        
        # Send back a success message and the new data
        return jsonify({
            'success': True,
            'link': {'title': new_link.title, 'url': new_link.url}
        })
        
    # If validation fails, send back the exact error messages
    return jsonify({
        'success': False,
        'errors': form.errors
    }), 400

@app.route('/api/update-link/<int:id>', methods=['POST'])
@login_required
def update_link(id):
    form = LinkForm() # Or whatever your form is named
    
    if form.validate_on_submit():
        # 1. Fetch the EXISTING link
        link_to_update = Link.query.get_or_404(id)
        
        # 2. Overwrite its data
        link_to_update.title = form.title.data
        link_to_update.url = form.url.data
        
        # 3. Commit (DO NOT use db.session.add() here)
        db.session.commit()
        
        return jsonify({'success': True})
        
    return jsonify({'success': False, 'errors': form.errors})

@app.route('/announcements/<int:id>')
@login_required
def announcement(id):
    announcement = Announcement.query.get_or_404(id)
    
    read_stats = {}
    
    # --- Heart Logic ---
    heart_counts = AnnouncementHeart.query.filter_by(announcement_id=id).count()
        
    # --- Read Receipt Logic (For the "Read by X" footer) ---
    read_count = AnnouncementRead.query.filter_by(announcement_id=id).count()
        
    if read_count > 0:
        first_read = AnnouncementRead.query.filter_by(announcement_id=id).first()
        first_user = User.query.get(first_read.user_id)
            
        # Format the name
        name_parts = first_user.name.split()
        if len(name_parts) > 1:
            display_name = f"{name_parts[0]} {name_parts[-1][0]}."
        else:
            display_name = first_user.name
                
        read_stats[id] = {
            'count': read_count,
            'first_reader': display_name
        }
    else:
        read_stats[id] = {
            'count': 0,
            'first_reader': None
        }

    # 4. Fetch the CURRENT USER'S specific interactions
    # FIX: Define this variable outside the if-statement so logged-out users don't crash the page!
    user_hearted = []
    
    if current_user.is_authenticated:
        # FIX: Filter by BOTH the user's ID and the announcement ID
        heart_record = AnnouncementHeart.query.filter_by(
            user_id=current_user.id, 
            announcement_id=id
        ).first()
        
        # FIX: If a record exists, append the ID so your HTML {% if announcement.id in user_hearted %} works
        if heart_record:
            user_hearted.append(id)
        
    # 5. Pass it all to the template
    return render_template('announcement.html', 
                           announcement=announcement, 
                           heart_counts=heart_counts, 
                           user_hearted=user_hearted,
                           read_stats=read_stats,
                           has_back_btn=True, 
                           is_dedicated_page=True,
                           page_title="Announcement")

@app.route('/announcements')
@login_required
def announcements():
    # 1. Fetch all announcements, newest first
    announcements = Announcement.query.order_by(Announcement.date_posted.desc()).all()
    
    # 2. Prepare empty containers for our frontend data
    heart_counts = {}
    user_hearted_ids = []
    read_stats = {}
    read_ids = [] # <-- NEW: Container for the logged-in user's read receipts
    
    # 3. Process data for EACH announcement
    for a in announcements:
        # --- Heart Logic ---
        count = AnnouncementHeart.query.filter_by(announcement_id=a.id).count()
        heart_counts[a.id] = count
        
        # --- Read Receipt Logic (For the "Read by X" footer) ---
        read_count = AnnouncementRead.query.filter_by(announcement_id=a.id).count()
        
        if read_count > 0:
            first_read = AnnouncementRead.query.filter_by(announcement_id=a.id).first()
            first_user = User.query.get(first_read.user_id)
            
            # Format the name
            name_parts = first_user.name.split()
            if len(name_parts) > 1:
                display_name = f"{name_parts[0]} {name_parts[-1][0]}."
            else:
                display_name = first_user.name
                
            read_stats[a.id] = {
                'count': read_count,
                'first_reader': display_name
            }
        else:
            read_stats[a.id] = {
                'count': 0,
                'first_reader': None
            }

    # 4. Fetch the CURRENT USER'S specific interactions
    if current_user.is_authenticated:
        # What have they hearted?
        user_hearts = AnnouncementHeart.query.filter_by(user_id=current_user.id).all()
        user_hearted_ids = [heart.announcement_id for heart in user_hearts]
        
        # What have they read? (For the NEW tag)
        read_records = AnnouncementRead.query.filter_by(user_id=current_user.id).all()
        read_ids = [record.announcement_id for record in read_records]
        
    # 5. Pass it all to the template
    return render_template('announcements.html', 
                           announcements=announcements, 
                           heart_counts=heart_counts, 
                           user_hearted_ids=user_hearted_ids,
                           read_stats=read_stats,
                           read_ids=read_ids, # <-- Pass the list to the template
                           is_dedicated_page=True,
                           page_title="Announcement")

@app.route('/update-entry/announcement/<int:id>', methods=['GET', 'POST'])
@login_required
def update_announcement(id):
    announcement_to_update = Announcement.query.get_or_404(id)
    form = AnnouncementForm()

    if form.validate_on_submit():
        # POST REQUEST: The form is valid, save the new data
        announcement_to_update.title = form.title.data
        announcement_to_update.content = form.content.data
        announcement_to_update.url = form.url.data

        db.session.commit()
        return redirect(url_for('announcements'))
        
    elif request.method == 'GET':
        # GET REQUEST: Pre-fill the form fields with the existing database data
        form.title.data = announcement_to_update.title
        form.content.data = announcement_to_update.content
        form.url.data = announcement_to_update.url
    else:
        # If it's a POST but validate_on_submit() failed, print the exact errors to the terminal!
        print("FORM VALIDATION FAILED:", form.errors)

    return render_template('update-announcement.html', form=form, has_back_btn=True, is_entry=True)

@app.route('/delete-entry/announcement/<int:id>', methods=['POST', 'DELETE'])
def delete_announcement(id):
    # Only allow the author (or an admin) to delete it
    announcement_to_delete = Announcement.query.get_or_404(id)
    
    if current_user.id != announcement_to_delete.user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        # 1. Delete all attached Read Receipts first
        AnnouncementRead.query.filter_by(announcement_id=id).delete()
        
        # 2. Delete all attached Hearts first
        AnnouncementHeart.query.filter_by(announcement_id=id).delete()

        remaining_announcement = Announcement.query.count()
        
        # 3. NOW it is safe to delete the actual announcement
        db.session.delete(announcement_to_delete)
        db.session.commit()

        return jsonify({'success': True, 'new_total': remaining_announcement})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/deadlines')
@login_required
def deadlines():
    # 1. Grab the exact UTC time, remove timezone info, and add 8 hours for PHT
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    ph_time = now_utc + timedelta(hours=8)
    
    # 2. Calculate the 24-hour grace period based on Philippine Time
    cutoff_time = ph_time - timedelta(days=1)
    
    # 1. What has the user already checked off?
    completed_ids = [c.deadline_id for c in DeadlineCompletion.query.filter_by(user_id=current_user.id).all()]
    
    # 2. Start the query: Only get tasks where the deadline is STILL IN THE FUTURE (or grace period)
    active_query = Deadline.query.filter(Deadline.due_date >= cutoff_time)
    
    # 3. Filter out the ones they already clicked "Done" on
    if completed_ids:
        active_query = active_query.filter(Deadline.id.notin_(completed_ids))
        
    active_deadlines = active_query.order_by(Deadline.due_date.asc()).all()

    # --- NEW: Give the date a clock (11:59 PM) so Jinja can do exact hour math ---
    for d in active_deadlines:
        if type(d.due_date) is date:
            d.due_datetime = datetime.combine(d.due_date, time(23, 59, 59))
        else:
            d.due_datetime = d.due_date

    # today = date.today()
    return render_template('deadlines.html', deadlines=active_deadlines, completed_ids=completed_ids, today=ph_time, is_dedicated_page=True, page_title="Deadline")

@app.route('/deadlines/archive')
def deadlines_archive():
    # 1. Grab the exact UTC time, remove timezone info, and add 8 hours for PHT
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    ph_time = now_utc + timedelta(hours=8)
    
    # 2. Calculate the 24-hour grace period based on Philippine Time
    cutoff_time = ph_time - timedelta(days=1)
    
    completed_ids = [c.deadline_id for c in DeadlineCompletion.query.filter_by(user_id=current_user.id).all()]
    
    # The Archive Logic: Show it if the deadline HAS PASSED **OR** if the user ALREADY FINISHED IT
    if completed_ids:
        archive_deadlines = Deadline.query.filter(
            or_(Deadline.due_date < cutoff_time, Deadline.id.in_(completed_ids))
        ).order_by(Deadline.due_date.desc()).all()
    else:
        archive_deadlines = Deadline.query.filter(Deadline.due_date < cutoff_time).order_by(Deadline.due_date.desc()).all()

    for d in archive_deadlines:
        if type(d.due_date) is date:
            d.due_datetime = datetime.combine(d.due_date, time(23, 59, 59))
        else:
            d.due_datetime = d.due_date

    # today = date.today()
    return render_template('deadlines-archive.html', deadlines=archive_deadlines, completed_ids=completed_ids, today=ph_time, is_dedicated_page=True, page_title="Deadline")

@app.route('/update-entry/deadline/<int:id>', methods=['GET', 'POST'])
@login_required
def update_deadline(id):
    deadline_to_update = Deadline.query.get_or_404(id)
    form = DeadlineForm()

    course = Course.query.all()

    form.course.choices = [(c.id, f"{c.code} | {c.title}") for c in course]

    if form.validate_on_submit():
        # POST REQUEST: The form is valid, save the new data
        deadline_to_update.course_id = form.course.data
        deadline_to_update.description = form.description.data
        deadline_to_update.category = form.category.data
        deadline_to_update.date_given = form.date_given.data
        deadline_to_update.due_date = form.due_date.data
        deadline_to_update.status = form.status.data
        deadline_to_update.note = form.note.data

        db.session.commit()
        return redirect(url_for('deadlines'))
        
    elif request.method == 'GET':
        # GET REQUEST: Pre-fill the form fields with the existing database data
        form.course.data = deadline_to_update.course_id
        form.description.data = deadline_to_update.description
        form.category.data = deadline_to_update.category
        deadline_to_update.date_given = form.date_given.data
        deadline_to_update.due_date = form.due_date.data
        deadline_to_update.status = form.status.data
        deadline_to_update.note = form.note.data
    else:
        # If it's a POST but validate_on_submit() failed, print the exact errors to the terminal!
        print("FORM VALIDATION FAILED:", form.errors)

    return render_template('update-deadline.html', form=form, has_back_btn=True, is_entry=True)

@app.route('/delete-entry/deadline/<int:id>', methods=['POST', 'DELETE'])
def delete_deadline(id):
    # Only allow the author (or an admin) to delete it
    deadline_to_delete = Deadline.query.get_or_404(id)
    
    # if current_user.id != deadline_to_delete.user_id:
    #     return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        db.session.delete(deadline_to_delete)
        db.session.commit()

        remaining_deadline = Deadline.query.count()

        return jsonify({'success': True, 'new_total': remaining_deadline})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/courses')
@login_required
def courses():
    courses_list = Course.query.order_by(Course.date_added).all()
    
    # 1. Setup a dictionary to hold schedules grouped by the days of the week
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    master_schedule = {day: [] for day in days_order}
    
    # 2. Fetch ALL schedules and join them with their Course data
    all_schedules = CourseSchedule.query.join(Course).all()
    
    # 3. Populate the dictionary
    for sched in all_schedules:
        master_schedule[sched.day].append({
            'course_code': sched.course.code,
            'course_title': sched.course.title,
            'instructor': sched.course.instructor,
            'start_time': sched.start_time,
            'end_time': sched.end_time,
            'room' : sched.room,
            'conflict': False # Default state
        })
        
    # 4. Sort and Check for Conflicts
    for day in days_order:
        # Sort the day's schedules chronologically by start_time
        master_schedule[day].sort(key=lambda x: x['start_time'])
        
        # Compare each schedule to the next one to find overlaps
        day_scheds = master_schedule[day]
        for i in range(len(day_scheds) - 1):
            current_class = day_scheds[i]
            next_class = day_scheds[i+1]
            
            # The Conflict Formula
            if current_class['start_time'] < next_class['end_time'] and current_class['end_time'] > next_class['start_time']:
                current_class['conflict'] = True
                next_class['conflict'] = True

    # 5. Clean up empty days so we don't render blank tables
    master_schedule = {day: scheds for day, scheds in master_schedule.items() if scheds}

    return render_template(
        'courses.html', 
        courses=courses_list, 
        master_schedule=master_schedule,
        is_dedicated_page=True, 
        page_title="Course"
    )

@app.route('/courses/<int:id>/add-schedule', methods=['GET', 'POST'])
@login_required
def add_course_schedule(id):
    course = Course.query.get_or_404(id)
    form = CourseScheduleForm()

    if form.validate_on_submit():
        new_course_schedule = CourseSchedule(
            course_id = course.id,
            day = form.day.data,
            start_time = form.start_time.data,
            end_time = form.end_time.data,
            room = form.room.data
        )

        form.day.data = ''
        form.start_time.data = ''
        form.end_time.data = ''
        form.room.data = ''

        db.session.add(new_course_schedule)
        db.session.commit()

        return redirect(url_for('courses'))

    return render_template('add-course-schedule.html', course=course, form=form, has_back_btn=True, is_entry=True)

@app.route('/update-entry/course/<int:id>', methods=['GET', 'POST'])
@login_required
def update_course(id):
    course_to_update = Course.query.get_or_404(id)
    form = CourseForm()

    if form.validate_on_submit():
        # POST REQUEST: The form is valid, save the new data
        course_to_update.code = form.code.data
        course_to_update.title = form.title.data
        course_to_update.instructor = form.instructor.data
        course_to_update.instructor_email = form.instructor_email.data
        course_to_update.units = form.units.data

        db.session.commit()
        return redirect(url_for('courses'))
        
    elif request.method == 'GET':
        # GET REQUEST: Pre-fill the form fields with the existing database data
        form.code.data = course_to_update.code
        form.title.data = course_to_update.title
        form.instructor.data = course_to_update.instructor
        form.instructor_email.data = course_to_update.instructor_email
        form.units.data = course_to_update.units
    else:
        # If it's a POST but validate_on_submit() failed, print the exact errors to the terminal!
        print("FORM VALIDATION FAILED:", form.errors)

    return render_template('update-course.html', form=form, has_back_btn=True, is_entry=True)

@app.route('/delete-entry/course/<int:id>', methods=['POST', 'DELETE'])
def delete_course(id):
    # Only allow the author (or an admin) to delete it
    course_to_delete = Course.query.get_or_404(id)
    
    # if current_user.id != course_to_delete.user_id:
    #     return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        db.session.delete(course_to_delete)
        db.session.commit()

        remaining_course = Course.query.count()
        units_total = sum(course.units for course in Course.query.all())

        return jsonify({'success': True, 'new_total': remaining_course, 'new_units': units_total })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/courses/<int:id>/update-schedule', methods=['GET', 'POST'])
@login_required
def update_course_schedule(id):
    form = CourseScheduleForm()
    schedule_to_update = CourseSchedule.query.get_or_404(id)
    course = Course.query.get_or_404(schedule_to_update.course_id)

    if form.validate_on_submit():
        # POST REQUEST: The form is valid, save the new data
        schedule_to_update.day = form.day.data
        schedule_to_update.start_time = form.start_time.data
        schedule_to_update.end_time = form.end_time.data
        schedule_to_update.room = form.room.data

        db.session.commit()
        return redirect(url_for('courses'))
        
    elif request.method == 'GET':
        # GET REQUEST: Pre-fill the form fields with the existing database data
        form.day.data = schedule_to_update.day
        form.start_time.data = schedule_to_update.start_time
        form.end_time.data = schedule_to_update.end_time
        form.room.data = schedule_to_update.room
    else:
        # If it's a POST but validate_on_submit() failed, print the exact errors to the terminal!
        print("FORM VALIDATION FAILED:", form.errors)

    return render_template('update-course-schedule.html', schedule_to_update=schedule_to_update, form=form, course=course, has_back_btn=True, is_entry=True)

@app.route('/delete-entry/course-schedule/<int:id>', methods=['POST', 'DELETE'])
@login_required
def delete_course_schedule(id):
    # Only allow the author (or an admin) to delete it
    schedule_to_delete = CourseSchedule.query.get_or_404(id)
    
    # if current_user.id != schedule_to_delete.user_id:
    #     return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        db.session.delete(schedule_to_delete)
        db.session.commit()

        # remaining_schedule = CourseSchedule.query.count()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/class-summaries/<int:id>', methods=['GET', 'POST'])
@login_required
def summary(id):
    # 1. Fetch ALL summaries, ordering by newest date first
    summary = ClassSummary.query.options(joinedload(ClassSummary.course))\
        .get_or_404(id)

    return render_template('summary.html', summary=summary, is_dedicated_page=True, page_title="Class Summary", has_back_btn=True)

@app.route('/delete-entry/class-summary/<int:id>', methods=['POST', 'DELETE'])
@login_required
def delete_summary(id):
    # Only allow the author (or an admin) to delete it
    summary_to_delete = ClassSummary.query.get_or_404(id)
    
    # if current_user.id != summary_to_delete.user_id:
    #     return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        db.session.delete(summary_to_delete)
        db.session.commit()

        remaining_summary = ClassSummary.query.count()

        return jsonify({'success': True, 'new_total': remaining_summary})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/class-summaries')
@login_required
def summaries():
    # 1. Get the requested year and week from the URL. 
    # If they aren't provided (like when you first click the sidebar), default to the current week.
    # 1. Grab the exact UTC time, remove timezone info, and add 8 hours for PHT
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    ph_time = now_utc + timedelta(hours=8)
    
    current_year, current_week, _ = ph_time.isocalendar()

    req_year = request.args.get('year', default=current_year, type=int)
    req_week = request.args.get('week', default=current_week, type=int)

    # 2. Calculate the exact calendar dates for Monday and Sunday of this specific week
    # .fromisocalendar() takes (Year, Week Number, Day of Week: 1=Monday, 7=Sunday)
    monday = date.fromisocalendar(req_year, req_week, 1)
    sunday = date.fromisocalendar(req_year, req_week, 7)

    # 3. Fetch ONLY the summaries that fall between this Monday and Sunday
    raw_summaries = ClassSummary.query.options(joinedload(ClassSummary.course))\
        .filter(ClassSummary.date_held >= monday, ClassSummary.date_held <= sunday)\
        .order_by(ClassSummary.date_held.desc()).all()

    total_count = len(raw_summaries)

    # 4. Your exact existing logic for grouping them by day goes here!
    grouped_summaries = {}
    for summary in raw_summaries:
        record_date = summary.date_held
        
        # (Keep your existing _sort_time logic here)
        
        if record_date not in grouped_summaries:
            grouped_summaries[record_date] = []
        grouped_summaries[record_date].append(summary)

    for date_key in grouped_summaries:
        grouped_summaries[date_key].sort(key=lambda x: getattr(x, '_sort_time', 0))

    # 5. Calculate the dates for the "Previous" and "Next" buttons
    prev_monday = monday - timedelta(days=7)
    next_monday = monday + timedelta(days=7)

    prev_year, prev_week, _ = prev_monday.isocalendar()
    next_year, next_week, _ = next_monday.isocalendar()

    return render_template('summaries.html', 
                           grouped_summaries=grouped_summaries, 
                           total_count=total_count,
                           monday=monday, sunday=sunday,
                           req_week=req_week,
                           prev_year=prev_year, prev_week=prev_week,
                           next_year=next_year, next_week=next_week,
                           is_dedicated_page=True, 
                           page_title="Class Summary")

@app.route('/add-entry/class-summary', methods=['GET', 'POST'])
@login_required
def add_summary():
    form = ClassSummaryForm()

    # 1. Populate the Course choices
    courses = Course.query.all()
    form.course.choices = [(c.id, f"{c.code} | {c.title}") for c in courses]
    
    # 2. Populate ALL schedules so WTForms validation passes on POST
    # (We will use JavaScript to hide/show the correct ones on the front-end)
    all_schedules = CourseSchedule.query.all()
    form.schedule.choices = [(s.id, f"{s.day} {s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}") for s in all_schedules]

    if form.validate_on_submit():
        new_summary = ClassSummary(
            course_id=form.course.data,
            schedule_id=form.schedule.data,
            content=form.content.data,
            date_held=form.date_held.data, 
            note=form.note.data
        )

        form.course.data = ''
        form.schedule.data = ''
        form.content.data = ''
        form.date_held.data = ''
        form.note.data = ''

        db.session.add(new_summary)

        # Grab all saved browser subscriptions from the database
        all_subscriptions = PushSubscription.query.all()
        
        for sub in all_subscriptions:
            # Use the helper method we made in models.py to turn the text back into a dictionary
            sub_dict = sub.get_subscription_dict()
            
            # Fire the message!
            status = send_web_push(
                subscription_dict=sub_dict, 
                notification_title="New Class Summary!", 
                notification_body=new_summary.content,
                target_url=f"/class-summaries#summary-{new_summary.id}"
            )

            # NEW: Automatically clean the database if the address is dead!
            if status == "expired":
                db.session.delete(sub)

        db.session.commit()

        return redirect(url_for('summaries'))
    else:
        print(form.errors)
    
    return render_template('add-summary.html', form=form, has_back_btn=True, is_entry=True)

@app.route('/update-entry/class-summary/<int:id>', methods=['GET', 'POST'])
@login_required
def update_summary(id):
    form = ClassSummaryForm()
    summary_to_update = ClassSummary.query.get_or_404(id)

    # 1. Populate the Course choices
    courses = Course.query.all()
    form.course.choices = [(c.id, f"{c.code} | {c.title}") for c in courses]
    
    # 2. Populate ALL schedules so WTForms validation passes on POST
    # (We will use JavaScript to hide/show the correct ones on the front-end)
    all_schedules = CourseSchedule.query.all()
    form.schedule.choices = [(s.id, f"{s.day} {s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}") for s in all_schedules]

    if form.validate_on_submit():
        # POST REQUEST: The form is valid, save the new data
        summary_to_update.course_id =  form.course.data
        summary_to_update.schedule_id = form.schedule.data
        summary_to_update.content = form.content.data
        summary_to_update.date_held = form.date_held.data 
        summary_to_update.note = form.note.data

        db.session.commit()
        return redirect(url_for('summaries'))
        
    elif request.method == 'GET':
        # GET REQUEST: Pre-fill the form fields with the existing database data
        form.course.data = summary_to_update.course_id
        form.schedule.data = summary_to_update.schedule_id
        form.content.data = summary_to_update.content
        form.date_held.data = summary_to_update.date_held 
        form.note.data = summary_to_update.note
    else:
        # If it's a POST but validate_on_submit() failed, print the exact errors to the terminal!
        print("FORM VALIDATION FAILED:", form.errors)
    
    return render_template('update-summary.html', summary_to_update=summary_to_update, form=form, has_back_btn=True, is_entry=True)

# --- NEW API ROUTE ---
# JavaScript will fetch data from here when a course is clicked
@app.route('/api/get-schedules/<int:course_id>')
@login_required
def get_schedules(course_id):
    schedules = CourseSchedule.query.filter_by(course_id=course_id).all()
    
    # Package the data into a JSON dictionary
    schedule_data = []
    for s in schedules:
        schedule_data.append({
            'id': s.id, 
            'label': f"{s.day} | {s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}"
        })
        
    return jsonify({'schedules': schedule_data})


@app.route('/links')
@login_required
def links():
    links = Link.query.all()

    return render_template('links.html', links=links, is_dedicated_page=True)

@app.route('/delete-entry/link/<int:id>', methods=['POST', 'DELETE'])
@login_required
def delete_link(id):
    # Only allow the author (or an admin) to delete it
    link_to_delete = Link.query.get_or_404(id)
    
    # if current_user.id != link_to_delete.user_id:
    #     return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        db.session.delete(link_to_delete)
        db.session.commit()

        remaining_link = Link.query.count()

        return jsonify({'success': True, 'new_total': remaining_link})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/notifications')
def notifications():
    # 1. Create an empty master list
    master_feed = []

    # 2. Fetch the 20 newest Announcements
    announcements = Announcement.query.order_by(Announcement.date_posted.desc()).limit(20).all()
    for a in announcements:
        master_feed.append({
            'type': 'Announcement',
            'title': a.title,
            'preview': a.content[:80] + '...' if len(a.content) > 80 else a.content, # Snippet
            'raw_date': a.date_posted,
            'url': f"/announcements#announcement-{a.id}",
            'icon': 'fa-bullhorn'
        })

    # 3. Fetch the 20 newest Deadlines
    # Using date_given as the "posted" date
    deadlines = Deadline.query.order_by(Deadline.date_given.desc()).limit(20).all()
    for d in deadlines:
        master_feed.append({
            'type': 'Deadline',
            'title': "New Deadline Posted",
            'preview': f"{d.course.code}: {d.description} (Due: {d.due_date.strftime('%b %d')})",
            'raw_date': d.date_given,
            'url': f"/deadlines#deadline-{d.id}",
            'icon': 'fa-clock'
        })

    # 4. Fetch the 20 newest Class Summaries
    summaries = ClassSummary.query.order_by(ClassSummary.date_held.desc()).limit(20).all()
    for s in summaries:
        master_feed.append({
            'type': 'Class Summary',
            'title': f"Summary Added: {s.course.code}",
            'preview': s.content[:80] + '...' if len(s.content) > 80 else s.content,
            'raw_date': s.date_held,
            'url': f"/class-summaries#summary-{s.id}",
            'icon': 'fa-book-open'
        })

    # 5. Fetch the 20 newest Link
    links = Link.query.order_by(Link.date_added.desc()).limit(20).all()
    for l in links:
        master_feed.append({
            'type': 'Class Link',
            'title': f"Link Added: {l.title}",
            'preview': l.url[:80] + '...' if len(l.url) > 80 else l.url,
            'raw_date': l.date_added,
            'url': f"/links#link-{l.id}",
            'icon': 'fa-link'
        })

    # 6. The Sorting Fix (Date vs. Datetime)
    # Python crashes if you try to sort a mix of 'dates' and 'datetimes'. 
    # This helper loop ensures everything is a comparable datetime object.
    for item in master_feed:
        if isinstance(item['raw_date'], datetime):
            item['sortable_date'] = item['raw_date']
        elif isinstance(item['raw_date'], date):
            # Convert a plain date (like Deadline.date_given) into a datetime at midnight
            item['sortable_date'] = datetime.combine(item['raw_date'], datetime.min.time())
        else:
            item['sortable_date'] = datetime.min # Fallback for missing dates

    # 7. Sort the master list (Newest items at the very top)
    master_feed.sort(key=lambda x: x['sortable_date'], reverse=True)

    # 8. Pass the final, sorted feed to your HTML
    return render_template(
        'notifications.html', 
        notifications=master_feed,
        is_dedicated_page=True,
        page_title="Notifications"
    )

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedbacks():
    feedback = Feedback.query.filter(Feedback.status == 'Pending').order_by(Feedback.date_added.desc()).all()

    user_feedback_count = Feedback.query.filter(current_user.id == Feedback.user_id, Feedback.status == 'Pending').count()

    return render_template('feedbacks.html', feedback=feedback, user_feedback_count=user_feedback_count)

@app.route('/feedback-archive', methods=['GET', 'POST'])
@login_required
def feedbacks_archive():
    feedback = Feedback.query.filter(Feedback.status == 'Resolved').order_by(Feedback.date_added.desc()).all()

    user_feedback_count = Feedback.query.filter(current_user.id == Feedback.user_id, Feedback.status == 'Resolved').count()

    return render_template('feedbacks-archive.html', feedback=feedback, user_feedback_count=user_feedback_count)
    
@app.route('/new-entry/feedback', methods=['GET', 'POST'])
def add_feedback():
    form = FeedbackForm()

    user_id = current_user.id if current_user.is_authenticated else None

    if form.validate_on_submit():
        new_feedback = Feedback(
            user_id = user_id,
            title = form.title.data,
            category = form.category.data,
            message = form.message.data
        )

        db.session.add(new_feedback)
        db.session.commit()

        return redirect(url_for('feedbacks'))
    elif request.method == 'POST':
        # If it's a POST request but validation failed, print the exact reason!
        print("FEEDBACK FORM FAILED:", form.errors)

    return render_template('add-feedback.html', form=form, has_back_btn=True) 

@app.route('/update-entry/feedback/<int:id>', methods=['GET', 'POST'])
@login_required
def update_feedback(id):
    form = FeedbackForm()
    feedback_to_update = Feedback.query.get_or_404(id)

    if form.validate_on_submit():
        feedback_to_update.user_id = current_user.id
        feedback_to_update.title = form.title.data
        feedback_to_update.category = form.category.data
        feedback_to_update.message = form.message.data

        db.session.commit()
        return redirect(url_for('feedbacks'))

    elif request.method == 'GET':
        form.title.data = feedback_to_update.title
        form.category.data = feedback_to_update.category 
        form.message.data = feedback_to_update.message

    else:
        print("FORM VALIDATION FAILED:", form.errors)

    return render_template('update-feedback.html', form=form, has_back_btn=True) 

@app.route('/api/reply-feedback/<int:id>', methods=['POST'])
@login_required
def reply_feedback(id):
    data = request.get_json()
    reply_text = data.get('reply_text', '').strip()
    
    feedback = Feedback.query.get_or_404(id)
    
    # Save the reply and update the status
    feedback.admin_reply = reply_text
    feedback.status = 'Resolved'
    
    db.session.commit()

    return jsonify({'success': True})

@app.route('/profile/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    form = ProfileForm()
    tag_form = CreateTagForm()

    # 1. DYNAMICALLY LOAD CHOICES
    # This fetches all tags and formats them as (id, name) for WTForms
    form.tags.choices = [(tag.id, tag.name) for tag in Tag.query.all()]

    if form.validate_on_submit():
        # 1. Update the text fields
        current_user.name = form.name.data
        current_user.bio = form.bio.data

        # 2. SAVE THE TAGS
        # Clear their old tags first
        current_user.tags = []

        # Loop through the integer IDs they checked and add the actual Tag objects
        for tag_id in form.tags.data:
            selected_tag = Tag.query.get(tag_id)
            if selected_tag:
                current_user.tags.append(selected_tag)

        # 2. Check if they uploaded a new image
        if form.profile_pic.data:
            image_file = form.profile_pic.data
            
            # Send it to Cloudinary directly!
            upload_result = cloudinary.uploader.upload(image_file, resource_type='image')
            
            # Save the new URL to the database
            current_user.profile_image = upload_result.get("secure_url")

        # 3. Save everything
        db.session.commit()
        return redirect(url_for('profile'))

    elif request.method == 'GET':
        # PRE-FILL THE FORM when they first load the page
        form.name.data = current_user.name
        form.bio.data = current_user.bio

        # 3. PRE-CHECK THE BOXES THEY ALREADY OWN
        form.tags.data = [tag.id for tag in current_user.tags]
    else:
        print("FORM VALIDATION FAILED:", form.errors)

    return render_template('update-profile.html', form=form, tag_form=tag_form, page_title="Profile", has_back_btn=True)

@app.route('/api/settings/update-email', methods=['POST'])
@login_required
def api_update_email():
    data = request.get_json()
    new_email = data.get('email')

    if not new_email:
        return jsonify({'success': False, 'message': 'Email is required.'}), 400

    # Check if someone else is already using this email
    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user and existing_user.id != current_user.id:
        return jsonify({'success': False, 'message': 'This email is already in use.'}), 400

    # Send the verification email instead of saving to the database
    try:
        send_verification_email(current_user, new_email)
        return jsonify({'success': True, 'message': 'Verification email sent! Please check your inbox.'})
    except Exception as e:
        print(f"Mail Error: {e}")
        return jsonify({'success': False, 'message': 'Failed to send email. Please try again later.'}), 500

@app.route('/api/settings/update-password', methods=['POST'])
@login_required
def api_update_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    # Use the helper method to verify the current password safely
    if not current_user.check_password(current_password):
        return jsonify({'success': False, 'message': 'Incorrect current password.'}), 403

    # Use the helper method to hash the new password
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password updated successfully!'})

@app.route('/api/settings/delete-account', methods=['DELETE'])
@login_required
def api_delete_account():
    user = User.query.get(current_user.id)
    
    # Optional: Log them out before deleting the record
    logout_user()
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'redirect': url_for('login')})


@app.route('/profile')
@login_required
def profile():
    form = LoginForm()
    # Inside your profile route...
    total_hearts = AnnouncementHeart.query.filter_by(user_id=current_user.id).count()
    # total_summaries = ClassSummary.query.filter_by(user_id=current_user.id).count()
    # (You would need to add a user_id to ClassSummary for this to work!)

    # Create a dynamic list to pass to the HTML
    earned_badges = []

    if total_hearts >= 5:
        earned_badges.append({'name': 'Active Supporter', 'description': 'React on 5 Posted Announcements' , 'icon': 'fa-heart', 'color': 'danger'})
        
    # if total_summaries >= 3:
    #     earned_badges.append({'name': 'Top Contributor', 'icon': 'fa-book-open', 'color': 'success'})
    
    return render_template('profile.html', earned_badges=earned_badges, form=form)

@app.route('/api/create-tag', methods=['POST'])
@login_required
def create_tag():
    form = CreateTagForm()
    
    # WTForms will automatically find the CSRF token and data in the request
    if form.validate_on_submit():
        
        # Check if the tag already exists (case-insensitive) to prevent duplicates
        existing_tag = Tag.query.filter(func.lower(Tag.name) == func.lower(form.tag_name.data)).first()
        
        if existing_tag:
            return jsonify({'success': False, 'error': 'This tag already exists!'}), 400

        # Save the new tag
        new_tag = Tag(
            name=form.tag_name.data,
            category=form.tag_category.data
        )
        db.session.add(new_tag)
        db.session.commit()
        
        # Send the success response with the new tag's data
        return jsonify({
            'success': True,
            'tag': {
                'id': new_tag.id,
                'name': new_tag.name,
                'category': new_tag.category
            }
        })
        
    # If WTForms validation fails
    return jsonify({'success': False, 'errors': form.errors}), 400

@app.route('/blockmates')
@login_required
def blockmates():
    # Fetch all users, maybe sort alphabetically by name
    all_students = User.query.order_by(User.name).all()
    return render_template('blockmates.html', students=all_students)

@app.route('/blockmates/<int:id>', methods=['GET', 'POST'])
@login_required
def blockmate(id):
    blockmate = User.query.get_or_404(id)

    # Create a dynamic list to pass to the HTML
    earned_badges = []
    total_hearts = AnnouncementHeart.query.filter_by(user_id=blockmate.id).count()

    if total_hearts >= 5:
        earned_badges.append({'name': 'Active Supporter', 'icon': 'fa-heart', 'color': 'danger'})

    return render_template('blockmate.html', blockmate=blockmate, earned_badges=earned_badges, has_back_btn=True)

@app.route('/tools/wallpaper')
@login_required
def wallpaper_generator():
    # 1. Fetch all schedules and join them with Course
    all_schedules = CourseSchedule.query.join(Course).all()
    
    # 2. Prepare a standard dictionary
    grouped_schedule = {}
    
    for sched in all_schedules:
        # THE FIX: Strip hidden spaces and force capitalization (e.g., ' monday ' -> 'Monday')
        day = sched.day.strip().capitalize()
        
        # If we haven't seen this day yet, create a list for it
        if day not in grouped_schedule:
            grouped_schedule[day] = []
            
        grouped_schedule[day].append({
            'time': f"{sched.start_time.strftime('%I:%M %p')} - {sched.end_time.strftime('%I:%M %p')}",
            'course': sched.course.code,
            'room': sched.room,
            'raw_time': sched.start_time # We keep this hidden value to sort chronologically 
        })
        
    # 3. Sort the days in order
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    sorted_schedule = {}
    
    for target_day in day_order:
        if target_day in grouped_schedule:
            # Sort the classes inside that day from morning to evening using the hidden raw_time
            sorted_classes = sorted(grouped_schedule[target_day], key=lambda x: x['raw_time'])
            sorted_schedule[target_day] = sorted_classes

    return render_template('wallpaper.html', schedule_data=sorted_schedule)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Check if the user exists AND the passwords match using Werkzeug
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            # Optional: Add a flash message here for invalid credentials
            pass
            
    return render_template('login.html', form=form, is_auth=True)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('dashboard'))

@app.route('/signup', methods=['GET', 'POST'])
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
            return redirect(url_for('dashboard'))
        
    return render_template('signup.html', form=form, is_auth=True)
    
@app.route('/verify-email/<token>')
@login_required
def verify_email_update(token):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    
    try:
        # Decrypt the token. Max_age=1800 means it expires in 1800 seconds (30 mins).
        data = serializer.loads(token, salt='email-update-salt', max_age=1800)
        
        user_id = data.get('user_id')
        new_email = data.get('new_email')
        
        # Security check: Ensure the logged-in user matches the token
        if current_user.id != user_id:
            flash('Invalid or unauthorized token.', 'danger')
            return redirect(url_for('settings'))

        # SUCCESS! Update the database.
        current_user.email = new_email
        db.session.commit()
        
        flash('Your email has been successfully updated!', 'success')
        return redirect(url_for('profile'))
        
    except SignatureExpired:
        flash('The verification link has expired. Please request a new one.', 'danger')
        return redirect(url_for('profile'))
        
    except BadSignature:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('profile'))
    

# RENDER ERROR PAGES
# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

