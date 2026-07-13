"""(Page Manager) - This is where the magic happens. It connects the URL (e.g., /dashboard) to the right HTML page."""

from flask import render_template, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, login_required, logout_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import date, timedelta

from app import app, login_manager, db

import cloudinary
import cloudinary.uploader

from app.models import User, Announcement, AnnouncementRead, AnnouncementHeart, ClassSummary, Course, Deadline, Link
from app.webforms import AnnouncementForm, ClassSummaryForm, CourseForm, DeadlineForm, LinkForm, LoginForm, SignupForm
from app.filter import markdown_filter, parse_links_filter, extract_images_filter, remove_images_filter

@login_manager.user_loader
def load_user(user_id):
    # This looks up the user in your database by their ID
    return User.query.get(int(user_id))

@app.context_processor
def inject_global_forms():
    """
    This makes the LinkForm available to every single HTML template automatically,
    so our global modal.html never crashes.
    """
    return dict(link_form=LinkForm())

@app.route('/complete-deadline/<int:id>', methods=['POST'])
def complete_deadline(id):
    data = request.get_json()
    is_completed = data.get('completed', False)
    
    deadline = Deadline.query.get_or_404(id)
    
    # Update the status based on the checkbox
    if is_completed:
        deadline.status = 'Done'
    else:
        deadline.status = 'Pending'
        
    db.session.commit()
    
    # Count the remaining active deadlines
    remaining_deadlines = Deadline.query.filter(
        Deadline.status.in_(['Upcoming', 'Pending'])
    ).count()

    # Count the totally completed deadlines
    archived_deadlines = Deadline.query.filter_by(status='Done').count()

    # Send BOTH totals back to the JavaScript
    return jsonify({    
        'success': True, 
        'new_total': remaining_deadlines,
        'archive_total': archived_deadlines
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
    
    total_deadlines = Deadline.query.filter(
        Deadline.status.in_(['Upcoming', 'Pending'])
    ).count()

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
    
    # class_summary = ClassSummary.query.order_by(ClassSummary.scheduled_date).all()

    # link = Link.query.order_by(Link.date_added).all()

    # ---------------------------------------------------------
    # 3. DEADLINES & OTHER DATA
    # ---------------------------------------------------------
    deadlines = Deadline.query.filter(
        Deadline.status.in_(['Upcoming', 'Pending'])
    ).order_by(Deadline.due_date).limit(3).all()
    
    links = Link.query.order_by(Link.date_added).all()

    today = date.today()

    # 1. Math: Sunday is 6. If today is Wed (2), 6 - 2 = 4 days until Sunday.
    days_until_sunday = 6 - today.weekday()
    
    # 2. Add those days to today's date to find the exact date of this Sunday
    end_of_week = today + timedelta(days=days_until_sunday)

    # 1. Grab the absolute newest record, regardless of time.
    target_record = ClassSummary.query.order_by(ClassSummary.scheduled_date.desc()).first()
    
    # 2. Create an empty dictionary to hold our grouped data
    daily_summaries = {}
    
    if target_record:
        # 2. Extract just the calendar date from the newest record
        record_date = target_record.scheduled_date
        if hasattr(record_date, 'date'):
            record_date = record_date.date()
            
        # 3. Calculate how many days old it is
        days_old = (date.today() - record_date).days
        
        # 4. If it is 3 days old or less, fetch all summaries for that calendar day
        if days_old <= 3:
            # 1. Fetch the raw summaries just like before
            raw_summaries = ClassSummary.query.options(joinedload(ClassSummary.course)).filter(
                func.date(ClassSummary.scheduled_date) == record_date
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
        deadlines=deadlines,
        total_deadlines=total_deadlines,
        target_record=target_record,
        daily_summaries=daily_summaries,
        links=links,
        user=user,
        today=today,
        end_of_week=end_of_week
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
        db.session.commit()

        return redirect(url_for('announcements'))

    return render_template('add-announcement.html', form=form, has_back_btn=True, is_entry=True)

@app.route('/add-entry/class-summary', methods=['GET', 'POST'])
def add_summary():
    form = ClassSummaryForm()

    course = Course.query.all()
    form.course.choices = [(c.id, f"{c.code} | {c.title}") for c in course]

    if form.validate_on_submit():
        new_summary = ClassSummary(
            course_id=form.course.data,
            content=form.content.data,
            scheduled_date=form.scheduled_date.data,
            note=form.note.data
        )

        form.course.data = ''
        form.content.data = ''
        form.scheduled_date.data = ''
        form.note.data = ''

        db.session.add(new_summary)
        db.session.commit()

        return redirect(url_for('summaries'))
    
    return render_template('add-summary.html', form=form, has_back_btn=True, is_entry=True)

@app.route('/add-entry/course', methods=['GET', 'POST'])
def add_course():
    form = CourseForm()

    if form.validate_on_submit():
        new_course = Course(
            code=form.code.data,
            title=form.title.data,
            instructor=form.instructor.data,
            units=form.units.data,
        )

        form.code.data = ''
        form.title.data = ''
        form.instructor.data = ''
        form.units.data = ''

        db.session.add(new_course)
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

@app.route('/announcements/<int:id>')
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
                           is_dedicated_page=True)

@app.route('/announcements')
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
                           is_dedicated_page=True)

@app.route('/update-entry/announcement/<int:id>', methods=['GET', 'POST'])
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
        
        # 3. NOW it is safe to delete the actual announcement
        db.session.delete(announcement_to_delete)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/deadlines')
def deadlines():
    deadlines = Deadline.query.filter(
        Deadline.status.in_(['Upcoming', 'Pending'])).order_by(Deadline.due_date).all()
    today = date.today()
    return render_template('deadlines.html', deadlines=deadlines, today=today, is_dedicated_page=True)

@app.route('/deadlines/archive')
def deadlines_archive():
    deadlines = Deadline.query.filter(
        Deadline.status.in_(['Done', 'Dropped'])).order_by(Deadline.due_date).all()
    today = date.today()
    return render_template('deadlines-archive.html', deadlines=deadlines, today=today, is_dedicated_page=True)

@app.route('/update-entry/deadline/<int:id>', methods=['GET', 'POST'])
def update_deadline(id):
    deadline_to_update = Deadline.query.get_or_404(id)
    form = DeadlineForm()

    if form.validate_on_submit():
        # POST REQUEST: The form is valid, save the new data
        deadline_to_update.course = form.course.data
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
        form.course.data = deadline_to_update.course
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

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/courses')
def courses():
    courses = Course.query.order_by(Course.date_added).all()
    return render_template('courses.html', courses=courses, is_dedicated_page=True)

@app.route('/class-summaries')
def summaries():
    summaries = ClassSummary.query.order_by(ClassSummary.date_added).all()
    return render_template('summaries.html', summaries=summaries, is_dedicated_page=True)




@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user:
            if password == user.password_hash:
                login_user(user)
                return redirect(url_for('dashboard'))
    
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('dashboard'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        name=form.name.data
        email=form.email.data
        password=form.password.data
        role=form.role.data

        user = User.query.filter_by(email=email).first()

        if user is None:
            new_user = User(
                name=name,
                email=email,
                password_hash=password,
                role=role
            )

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
        
        form.name.data = ''
        form.email.data = ''
        form.password.data = ''
        form.confirm_password.data = ''
        form.role.data = ''

        return redirect(url_for('dashboard'))
    
    return render_template('signup.html', form=form)