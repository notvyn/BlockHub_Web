"""(Page Manager) - This is where the magic happens. It connects the URL (e.g., /dashboard) to the right HTML page."""

from flask import render_template, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, login_required, logout_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import date, timedelta
from markupsafe import Markup
import markdown

from app import app, login_manager, db

from app.models import User, Announcement, AnnouncementRead, ClassSummary, Course, Deadline, Link
from app.webforms import AnnouncementForm, ClassSummaryForm, CourseForm, DeadlineForm, LinkForm, LoginForm, SignupForm

@login_manager.user_loader
def load_user(user_id):
    # This looks up the user in your database by their ID
    return User.query.get(int(user_id))

# Add this custom filter to your Flask app
@app.template_filter('markdown')
def markdown_filter(text):
    # This converts the Markdown to HTML, and Markup() tells Jinja it is safe to render
    return Markup(markdown.markdown(text))

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
    
    # NEW LOGIC: Calculate the true total of remaining deadlines in the database
    remaining_deadlines = Deadline.query.filter(
        Deadline.status.in_(['Upcoming', 'Pending'])
    ).count()

    # Send that true total back to the JavaScript
    return jsonify({    
        'success': True, 
        'new_total': remaining_deadlines
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

@app.route('/', methods=['GET', 'POST'])
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    announcement_form = AnnouncementForm()
    class_summary_form = DeadlineForm()
    deadline_form = DeadlineForm()
    link_form = LinkForm()
    
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
        link_form=link_form,
        user=user,
        today=today,
        end_of_week=end_of_week,
        is_entry=True
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

        return redirect(url_for('add_announcement'))

    return render_template('add-announcement.html', form=form)

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

        return redirect(url_for('add_summary'))
    return render_template('add-summary.html', form=form)

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

        return redirect(url_for('add_course'))
    
    return render_template('add-course.html', form=form)

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

        return redirect(url_for('add_deadline'))

    return render_template('add-deadline.html', form=form)

@app.route('/add-entry/link', methods=['GET', 'POST'])
def add_link():
    form = LinkForm()

    if form.validate_on_submit():
        new_link = Link(
            title=form.title.data,
            url=form.url.data
        )

        form.title.data = ''
        form.url.data = ''

        db.session.add(new_link)
        db.session.commit()

        return redirect(url_for('add_link'))

    return render_template('add-link.html', form=form)

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
    return render_template('announcement.html', announcement=announcement)

@app.route('/announcements')
def announcements():
    announcements = Announcement.query.order_by(Announcement.date_posted.desc()).all()
    return render_template('announcements.html', announcements=announcements, is_entry=True, is_dedicated_page=True)

@app.route('/deadlines')
def deadlines():
    deadlines = Deadline.query.order_by(Deadline.due_date).all()
    today = date.today()
    return render_template('deadlines.html', deadlines=deadlines, today=today, is_entry=True, is_dedicated_page=True)

@app.route('/courses')
def courses():
    courses = Course.query.order_by(Course.date_added).all()
    return render_template('courses.html', courses=courses, is_entry=True, is_dedicated_page=True)

@app.route('/class-summaries')
def summaries():
    summaries = ClassSummary.query.order_by(ClassSummary.date_added).all()
    return render_template('summaries.html', summaries=summaries, is_entry=True, is_dedicated_page=True)


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