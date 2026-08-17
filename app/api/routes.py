from flask import jsonify, url_for, request
from flask_login import current_user, login_required, logout_user
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename
from datetime import datetime
import cloudinary, cloudinary.uploader, json, os, uuid

from app import db

from app.forms import CreateTagForm, LinkForm
from app.models import Announcement, AnnouncementHeart, AnnouncementRead, ClassSummary, Course, CourseSchedule, Deadline, DeadlineCompletion, Feedback, Link, PushSubscription, Tag, User
from app.utils import extract_schedule_from_pdf, send_verification_email, send_web_push

from app.api import api

@api.route('/api/add-link', methods=['POST'])
def add_link_api():
    form = LinkForm()
    
    # WTForms automatically checks the CSRF token and the URL format here!
    if form.validate_on_submit():
        new_link = Link(
            title=form.title.data, 
            url=form.url.data,
            category=form.category.data
            # user_id=current_user.id  # If your links are tied to specific users
        )
        db.session.add(new_link)

        # Grab all saved browser subscriptions from the database
        all_subscriptions = PushSubscription.query.all()
        
        for sub in all_subscriptions:
            # Use the helper method we made in models.py to turn the text back into a dictionary
            sub_dict = sub.get_subscription_dict()
            
            # Fire the message
            status = send_web_push(
                subscription_dict=sub_dict, 
                notification_title="New Class Link!", 
                notification_body=new_link.title,
                target_url=f"/links#link-{new_link.id}"
            )

            # Automatically clean the database if the address is dead!
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

@api.route('/api/settings/delete-account', methods=['DELETE'])
@login_required
def api_delete_account():
    user = User.query.get(current_user.id)
    
    # Log them out before deleting the record
    logout_user()
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'redirect': url_for('auth.login')})

@api.route('/api/settings/update-email', methods=['POST'])
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

    try:
        # Specify the action here
        send_verification_email(current_user, new_email, action='update_email')
        return jsonify({'success': True, 'message': 'Verification email sent! Please check your inbox.'})
    except Exception as e:
        print(f"Mail Error: {e}")
        return jsonify({'success': False, 'message': 'Failed to send email. Please try again later.'}), 500

@api.route('/api/settings/update-password', methods=['POST'])
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

@api.route('/api/bulk-import-schedule', methods=['POST'])
@login_required 
def bulk_import_schedule():
    if 'schedule_pdf' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded.'}), 400

    try:
        # Call the EXACT same parsing logic
        parsed_data = extract_schedule_from_pdf(request.files['schedule_pdf'])
        classes_added = 0
        
        # Iterate through the clean data
        for day, classes in parsed_data.items():
            for c in classes:
                course_code = c['course']
                room = c['room']
                
                # Split and convert "07:30 AM - 09:00 AM" into Python time objects
                time_parts = c['time'].split('-')
                start_str = time_parts[0].strip()
                end_str = time_parts[1].strip() if len(time_parts) > 1 else start_str
                
                start_time_obj = datetime.strptime(start_str, "%I:%M %p").time()
                end_time_obj = datetime.strptime(end_str, "%I:%M %p").time()

                # Verify or Create the Course
                course = Course.query.filter_by(code=course_code).first()
                if not course:
                    # Fill in defaults if the PDF has a new course not yet in the DB
                    course = Course(code=course_code, title="TBA", instructor="TBA", units=3.0) 
                    db.session.add(course)
                    db.session.flush() # Get the new ID without committing yet

                # Prevent Duplicates! Check if this exact schedule already exists
                existing_schedule = CourseSchedule.query.filter_by(
                    course_id=course.id,
                    day=day,
                    start_time=start_time_obj,
                    end_time=end_time_obj
                ).first()

                if not existing_schedule:
                    new_schedule = CourseSchedule(
                        course_id=course.id,
                        day=day,
                        start_time=start_time_obj,
                        end_time=end_time_obj,
                        room=room
                    )
                    db.session.add(new_schedule)
                    classes_added += 1

        # Commit everything to the database
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Successfully imported {classes_added} new classes!'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Bulk Import Error: {e}")
        return jsonify({'success': False, 'error': 'Failed to save schedules to the database.'}), 500

@api.route('/complete-deadline/<int:id>', methods=['POST'])
@login_required
def complete_deadline(id):
    data = request.get_json()
    is_completed = data.get('completed', False)

    # Check if a completion record already exists for THIS user and THIS deadline
    completion = DeadlineCompletion.query.filter_by(user_id=current_user.id, deadline_id=id).first()

    # Add or Remove the record based on the checkbox state
    if is_completed and not completion:
        # Checkbox was checked (true), and no record exists -> CREATE IT
        new_completion = DeadlineCompletion(user_id=current_user.id, deadline_id=id)
        db.session.add(new_completion)
        
    elif not is_completed and completion:
        # Checkbox was unchecked (false), and a record exists -> DELETE IT
        db.session.delete(completion)
    
    # Save the changes to the database
    db.session.commit()

    # Calculate the new badge totals dynamically for the JS to update the UI
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

@api.route('/complete-feedback/<int:id>', methods=['POST'])
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

@api.route('/api/complete-onboarding', methods=['POST'])
@login_required
def complete_onboarding():
    current_user.is_onboarded = True
    db.session.commit()
    return jsonify({'success': True})

@api.route('/api/create-tag', methods=['POST'])
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

@api.route('/delete-entry/announcement/<int:id>', methods=['POST', 'DELETE'])
def delete_announcement(id):
    # Only allow the author (or an admin) to delete it
    announcement_to_delete = Announcement.query.get_or_404(id)
    
    if current_user.id != announcement_to_delete.user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        # Delete all attached Read Receipts first
        AnnouncementRead.query.filter_by(announcement_id=id).delete()
        
        # Delete all attached Hearts first
        AnnouncementHeart.query.filter_by(announcement_id=id).delete()

        remaining_announcement = Announcement.query.count()
        
        # NOW it is safe to delete the actual announcement
        db.session.delete(announcement_to_delete)
        db.session.commit()

        return jsonify({'success': True, 'new_total': remaining_announcement})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/delete-entry/course/<int:id>', methods=['POST', 'DELETE'])
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

@api.route('/delete-entry/course-schedule/<int:id>', methods=['POST', 'DELETE'])
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

@api.route('/delete-entry/deadline/<int:id>', methods=['POST', 'DELETE'])
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

@api.route('/delete-entry/feedback/<int:id>', methods=['POST', 'DELETE'])
@login_required
def delete_feedback(id):
    # Only allow the author (or an admin) to delete it
    feedback_to_delete = Feedback.query.get_or_404(id)
    
    # if current_user.id != feedback_to_delete.user_id:
    #     return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        db.session.delete(feedback_to_delete)
        db.session.commit()

        remaining_feedback = Feedback.query.count()

        return jsonify({'success': True, 'new_total': remaining_feedback})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/delete-entry/link/<int:id>', methods=['POST', 'DELETE'])
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

@api.route('/delete-entry/class-summary/<int:id>', methods=['POST', 'DELETE'])
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

@api.route('/tag/<int:tag_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
        
    db.session.delete(tag)
    db.session.commit()
    
    # Return a success JSON instead of a redirect!
    return jsonify({'success': True})

@api.route('/tag/<int:tag_id>/edit', methods=['POST'])
@login_required
def edit_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    tag_form = CreateTagForm()
    
    if tag_form.validate_on_submit():
        tag.name = tag_form.tag_name.data
        tag.category = tag_form.tag_category.data
        db.session.commit()
        # Return a JSON success instead of a redirect
        return jsonify({'success': True})
        
    # Return JSON errors if validation fails
    return jsonify({'success': False, 'errors': tag_form.errors})

# JavaScript will fetch data from here when a course is clicked
@api.route('/api/get-schedules/<int:course_id>')
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

@api.route('/api/search')
@login_required # Keeps search data private to logged-in users
def global_search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'results': []})
        
    search_term = f"%{query}%"
    results = []

    # Search Links
    links = Link.query.filter(Link.title.ilike(search_term)).limit(3).all()
    for link in links:
        results.append({'type': 'Link', 'title': link.title, 'url': f"{url_for('main.links')}#link-{link.id}", 'icon': 'fa-link'})

    # Search Announcements
    announcements = Announcement.query.filter(
        or_(Announcement.title.ilike(search_term), Announcement.content.ilike(search_term))
    ).limit(3).all()
    for a in announcements:
        results.append({'type': 'Announcement', 'title': a.title, 'url': url_for('main.announcement', id=a.id), 'icon': 'fa-bullhorn'})

    # Search Deadlines
    deadlines = Deadline.query.filter(Deadline.description.ilike(search_term)).limit(3).all()
    for d in deadlines:
        results.append({'type': 'Deadline', 'title': d.description, 'url': f"{url_for('main.deadlines')}#deadline-{d.id}", 'icon': 'fa-clock'})

    # Search Class Summaries
    summaries = ClassSummary.query.filter(ClassSummary.content.ilike(search_term)).limit(3).all()
    for s in summaries:
        results.append({'type': 'Summary', 'title': f"{s.course.code} Summary", 'url': url_for('main.summary', id=s.id), 'icon': 'fa-book-open'})

    courses = Course.query.filter(
        or_(Course.code.ilike(search_term), Course.title.ilike(search_term), or_(Course.instructor.ilike(search_term)))
    ).limit(3).all()
    for c in courses:
        results.append({'type': 'Course', 'title': f"{c.code} | {c.title}", 'url': f"{url_for('main.courses')}#course-{c.id}", 'icon': 'fa-address-book'})

    return jsonify({'results': results})

@api.route('/mark-announcement-read/<int:id>', methods=['POST'])
@login_required
def mark_read(id):
    # Check if a receipt already exists so we don't make duplicates
    existing_receipt = AnnouncementRead.query.filter_by(
        user_id=current_user.id, 
        announcement_id=id
    ).first()
    
    # If not, create one
    if not existing_receipt:
        receipt = AnnouncementRead(user_id=current_user.id, announcement_id=id)
        db.session.add(receipt)
        db.session.commit()
        
    return {"status": "success"} # We just return a tiny dictionary, no HTML template

@api.route('/api/parse-schedule', methods=['POST'])
def parse_schedule():
    if 'schedule_pdf' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded.'}), 400

    try:
        # Call the shared helper function!
        parsed_data = extract_schedule_from_pdf(request.files['schedule_pdf'])

        # Prepare the secondary grouping for the Accordion UI
        course_data = {}
        for day, classes in parsed_data.items():
            for c in classes:
                course_code = c['course']
                if course_code not in course_data:
                    course_data[course_code] = {'title': 'Imported', 'classes': []}
                course_data[course_code]['classes'].append(c)

        return jsonify({'success': True, 'data': parsed_data, 'course_data': course_data})

    except Exception as e:
        print(f"PDF Parse Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api.route('/api/reply-feedback/<int:id>', methods=['POST'])
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

@api.route('/api/reset-onboarding', methods=['POST'])
@login_required
def reset_onboarding():
    current_user.is_onboarded = False
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Onboarding reset! Visit the dashboard to see the tour.'})

@api.route('/api/save-subscription', methods=['POST'])
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

@api.route('/sync-guest-reads', methods=['POST'])
@login_required
def sync_guest_reads():
    # Catch the JSON data sent by JavaScript
    data = request.get_json()
    
    # Extract the list of IDs (or default to an empty list)
    announcement_ids = data.get('ids', [])
    
    # Loop through the IDs and save them to the database
    for a_id in announcement_ids:
        # Check if the receipt already exists so we don't cause a database error
        existing = AnnouncementRead.query.filter_by(
            user_id=current_user.id, 
            announcement_id=a_id
        ).first()
        
        if not existing:
            receipt = AnnouncementRead(user_id=current_user.id, announcement_id=a_id)
            db.session.add(receipt)
            
    # Commit all the new receipts at once
    db.session.commit()
    
    return jsonify({"status": "success"})

@api.route('/toggle-heart/<int:announcement_id>', methods=['POST'])
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

@api.route('/api/toggle-link-pin/<int:id>', methods=['POST'])
@login_required
def toggle_link_pin(id):
    link_to_pin = Link.query.get_or_404(id)
    
    # Toggle the boolean value
    link_to_pin.is_pinned = not link_to_pin.is_pinned
    db.session.commit()
    
    return jsonify({'success': True, 'is_pinned': link_to_pin.is_pinned})

@api.route('/api/toggle-pin/<int:id>', methods=['POST'])
@login_required
def toggle_pin(id):
    announcement = Announcement.query.get_or_404(id)
    
    # Security: Ensure only the author can pin their own announcements
    # if announcement.user_id != current_user.id:
    #     return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    # Toggle the boolean value
    announcement.is_pinned = not announcement.is_pinned
    db.session.commit()
    
    # Return the new status so the frontend knows which icon to show
    return jsonify({'success': True, 'is_pinned': announcement.is_pinned})

@api.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    
    try:
        # Safely extract the original name and extension (e.g., "Test", ".docx")
        original_filename = secure_filename(file.filename) or "uploaded_file"
        name, ext = os.path.splitext(original_filename)
        
        # Generate a random 8-character string so users don't overwrite each other's files
        random_id = uuid.uuid4().hex[:8]
        
        # Smart ID Generation
        # List of common media formats that Cloudinary handles automatically
        media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mov']
        
        if ext.lower() in media_extensions:
            # For Images/Videos: Cloudinary adds the extension to the URL itself
            custom_public_id = f"{name}_{random_id}"
        else:
            # THE For Raw files (.docx, .pdf, .zip): We MUST force the extension into the ID
            custom_public_id = f"{name}_{random_id}{ext}"
            
        upload_result = cloudinary.uploader.upload(
            file, 
            resource_type='auto',
            public_id=custom_public_id
        )
        
        image_url = upload_result.get("secure_url")
        
        return jsonify({'data': {'filePath': image_url}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/api/update-link/<int:id>', methods=['POST'])
@login_required
def update_link(id):
    form = LinkForm() # Or whatever your form is named
    
    if form.validate_on_submit():
        # Fetch the EXISTING link
        link_to_update = Link.query.get_or_404(id)
        
        # Overwrite its data
        link_to_update.title = form.title.data
        link_to_update.url = form.url.data
        link_to_update.category = form.category.data
        
        # Commit (DO NOT use db.session.add() here)
        db.session.commit()
        
        return jsonify({'success': True})
        
    return jsonify({'success': False, 'errors': form.errors})