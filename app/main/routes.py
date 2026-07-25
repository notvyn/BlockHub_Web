from flask import render_template, redirect, url_for, send_from_directory, request
from flask_login import current_user, login_required
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime, timedelta, timezone, time

from app import db
from app.main import main

import cloudinary, cloudinary.uploader, os

from app.models import User, Announcement, AnnouncementRead, AnnouncementHeart, ClassSummary, Course, CourseSchedule, Deadline, Link, PushSubscription, Feedback, Tag, DeadlineCompletion
from app.forms import AnnouncementForm, ClassSummaryForm, CourseForm, CourseScheduleForm, DeadlineForm, LinkForm, LoginForm, FeedbackForm, ProfileForm, CreateTagForm
from app.filters import markdown_filter, parse_links_filter, extract_images_filter, remove_images_filter, time_ago_filter
from app.utils import send_web_push

def check_earned_badges(user_id):

    total_hearts = AnnouncementHeart.query.filter_by(user_id=user_id).count()
    total_suggestion = Feedback.query.filter(Feedback.user_id == user_id, Feedback.category == 'Suggestion').count()
    total_bug = Feedback.query.filter(Feedback.user_id == user_id, Feedback.category == 'Bug').count()
    total_deadlines = DeadlineCompletion.query.filter(DeadlineCompletion.user_id == user_id).count()

    # Create a dynamic list to pass to the HTML
    earned_badges = []

    if total_hearts >= 5:
        earned_badges.append({'name': 'Active Supporter', 'description': 'React on 5 Posted Announcements', 'icon': 'fa-hand-holding-heart', 'color': 'danger'})

    if total_deadlines == 5:
        earned_badges.append({'name': 'Achiever', 'description': 'Complete 5 Deadline Tasks', 'icon': 'fa-circle-check', 'color': 'success'})

    if total_suggestion >= 3:
        earned_badges.append({'name': 'Visionary', 'description': 'Suggest 3 ideas on Feedbacks', 'icon': 'fa-lightbulb', 'color': 'warning'})

    if total_bug >= 1:
        earned_badges.append({'name': 'Bug Finder', 'description': 'Find a bug on the program', 'icon': 'fa-bug-slash', 'color': 'secondary'})

    return earned_badges

# --- GLOBAL CONTEXT PROCESSORS ---
# Put this alongside your other routes!
@main.route('/sw.js')
def serve_sw():
    # This tells Flask to serve the file from the static folder, 
    # but the browser will think it's at the root (http://localhost:5000/sw.js)
    return send_from_directory('static', 'js/sw.js', mimetype='application/javascript')



# 1. Deals only with global forms
@main.app_context_processor
def inject_global_forms():
    """Makes LinkForm available everywhere for the global modal."""
    return dict(link_form=LinkForm())

@main.app_context_processor
def inject_course_state():
    """Makes 'has_courses' available globally to toggle UI elements."""
    # Using .first() is highly optimized. It just checks if AT LEAST ONE course 
    # exists without downloading the entire table into memory!
    has_courses = Course.query.first() is not None
    return dict(has_courses=has_courses)

# 2. Deals only with dynamic user data
@main.app_context_processor
def inject_global_badges():
    """Calculates notification badges for the sidebar."""
    badges = {}
    
    if current_user.is_authenticated:
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        ph_time = now_utc + timedelta(hours=8)
        
        # --- DEADLINES BADGE ---
        cutoff = ph_time - timedelta(days=1)
        completed = [c.deadline_id for c in DeadlineCompletion.query.filter_by(user_id=current_user.id).all()]
        
        active_query = Deadline.query.filter(Deadline.due_date >= cutoff)
        if completed:
            active_query = active_query.filter(Deadline.id.notin_(completed))
            
        badges['deadlines'] = active_query.count()

        # 1. Get the list of IDs the user has already read
        read_records = AnnouncementRead.query.filter_by(user_id=current_user.id).all()
        read_ids = [record.announcement_id for record in read_records]

        # 2. Count the announcements that are NOT in that list
        if read_ids:
            unread_count = Announcement.query.filter(Announcement.id.notin_(read_ids)).count()
        else:
            # If they haven't read anything, then EVERY announcement is unread!
            unread_count = Announcement.query.count()

        badges['announcements'] = unread_count
        
        # --- SUMMARIES BADGE (With Fallback for Existing Users) ---
        # Defaults to datetime.min if the database returns None
        last_summaries = current_user.last_viewed_summaries or datetime.min
        badges['summaries'] = ClassSummary.query.filter(ClassSummary.date_added > last_summaries).count()
        
        # --- LINKS BADGE (With Fallback for Existing Users) ---
        last_links = current_user.last_viewed_links or datetime.min
        badges['links'] = Link.query.filter(Link.date_added > last_links).count()

    return dict(badges=badges)

# --- DEDICATED PAGES --- 
@main.route('/', methods=['GET', 'POST'])
@main.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    announcement_form = AnnouncementForm()
    class_summary_form = DeadlineForm()
    deadline_form = DeadlineForm()

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

        # 1. Fetch up to 3 UNREAD announcements (Newest first)
        if read_announcement_ids:
            unread_announcements = Announcement.query.filter(
                ~Announcement.id.in_(read_announcement_ids)
            ).order_by(Announcement.date_posted.desc()).limit(3).all()
        else:
            # If the user hasn't read anything yet, everything is unread
            unread_announcements = Announcement.query.order_by(Announcement.date_posted.desc()).limit(3).all()

        final_announcements = unread_announcements

        # 2. If there are less than 3 unread, fill the gap with the newest READ announcements
        if len(final_announcements) < 3 and read_announcement_ids:
            gap = 3 - len(final_announcements)
            read_announcements = Announcement.query.filter(
                Announcement.id.in_(read_announcement_ids)
            ).order_by(Announcement.date_posted.desc()).limit(gap).all()
            
            final_announcements.extend(read_announcements)

        # 3. Sort the final combined list of 3 chronologically 
        final_announcements.sort(key=lambda x: x.date_posted, reverse=True)
        
    else:
        user = None
        # Fallback for logged-out users
        final_announcements = Announcement.query.order_by(Announcement.date_posted.desc()).limit(3).all()

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

    links = Link.query.order_by(Link.is_pinned.desc(), Link.date_added.desc()).all()

    # 1. Grab the exact UTC time, remove timezone info, and add 8 hours for PHT
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    ph_time = now_utc + timedelta(hours=8)
    
    # 2. Calculate the 24-hour grace period based on Philippine Time
    cutoff_time = ph_time - timedelta(days=1)

    # 1. Math: Sunday is 6. If today is Wed (2), 6 - 2 = 4 days until Sunday.
    # days_until_sunday = 6 - ph_time.weekday()
    
    # 2. Add those days to today's date to find the exact date of this Sunday
    # end_of_week = ph_time + timedelta(days=days_until_sunday)

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
        days_old = (ph_time.date() - record_date).days
        
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
        completed_ids=completed_ids
    )

@main.route('/announcements/<int:id>')
@login_required
def announcement(id):
    announcement = Announcement.query.get_or_404(id)
    
    # --- NEW: BACKEND READ RECEIPT SAFETY NET ---
    # Automatically mark as read if they view the dedicated page
    if current_user.is_authenticated:
        existing_receipt = AnnouncementRead.query.filter_by(
            user_id=current_user.id, 
            announcement_id=id
        ).first()
        
        if not existing_receipt:
            receipt = AnnouncementRead(user_id=current_user.id, announcement_id=id)
            db.session.add(receipt)
            db.session.commit()
    # ---------------------------------------------
    
    read_stats = {}
    
    # --- Heart Logic ---
    heart_counts = AnnouncementHeart.query.filter_by(announcement_id=id).count()
        
    # --- Read Receipt Logic (Excluding current_user) ---
    read_records = AnnouncementRead.query.filter_by(announcement_id=id).all()
    readers = []
    seen_user_ids = set()
    
    for record in read_records:
        # Skip the current user so they don't see themselves in the read list
        if current_user.is_authenticated and record.user_id == current_user.id:
            continue
            
        if record.user_id not in seen_user_ids:
            reader_user = User.query.get(record.user_id)
            if reader_user:
                readers.append(reader_user)
                seen_user_ids.add(record.user_id)
            
    read_stats[id] = {
        'count': len(read_records), # Keeps the true global total count (e.g. "Seen by 5")
        'readers': readers          # But only shows other people's avatars in the facepile
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

@main.route('/announcements')
@login_required
def announcements():
    # 1. Fetch all announcements, newest first
    announcements = Announcement.query.order_by(
        Announcement.is_pinned.desc(), 
        Announcement.date_posted.desc()
    ).all()
    
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
        
        # --- Read Receipt Logic (Excluding current_user) ---
        read_records = AnnouncementRead.query.filter_by(announcement_id=a.id).all()
        readers = []
        seen_user_ids = set()
        
        for record in read_records:
            # Skip the current user here as well
            if current_user.is_authenticated and record.user_id == current_user.id:
                continue
                
            if record.user_id not in seen_user_ids:
                reader_user = User.query.get(record.user_id)
                if reader_user:
                    readers.append(reader_user)
                    seen_user_ids.add(record.user_id)
                
        read_stats[a.id] = {
            'count': len(read_records),
            'readers': readers
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

@main.route('/blockmates')
@login_required
def blockmates():
    # Fetch all users, maybe sort alphabetically by name
    all_students = User.query.order_by(User.name).all()
    return render_template('blockmates.html', students=all_students)

@main.route('/blockmates/<int:id>', methods=['GET', 'POST'])
@login_required
def blockmate(id):
    blockmate = User.query.get_or_404(id)

    # Create a dynamic list to pass to the HTML
    earned_badges = check_earned_badges(blockmate.id)

    return render_template('blockmate.html', blockmate=blockmate, earned_badges=earned_badges, has_back_btn=True)

@main.route('/courses')
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

@main.route('/deadlines')
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

    total_deadlines = Deadline.query.count()

    # --- NEW: Give the date a clock (11:59 PM) so Jinja can do exact hour math ---
    for d in active_deadlines:
        if type(d.due_date) is date:
            d.due_datetime = datetime.combine(d.due_date, time(23, 59, 59))
        else:
            d.due_datetime = d.due_date

    # today = date.today()
    return render_template('deadlines.html', deadlines=active_deadlines, completed_ids=completed_ids, total_deadlines=total_deadlines, today=ph_time, is_dedicated_page=True, page_title="Deadline")

@main.route('/deadlines/archive')
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

@main.route('/feedback/<int:id>', methods=['GET', 'POST'])
@login_required
def feedback(id):
    feedback = Feedback.query.get_or_404(id)

    return render_template('feedback.html', feedback=feedback, has_back_btn=True)

@main.route('/feedbacks', methods=['GET', 'POST'])
@login_required
def feedbacks():
    feedback = Feedback.query.filter(Feedback.status == 'Pending').order_by(Feedback.date_added.desc()).all()

    user_total_feedback_count = Feedback.query.filter(current_user.id == Feedback.user_id).count()
    user_total_pending = Feedback.query.filter(current_user.id == Feedback.user_id, Feedback.status == 'Pending').count()
    total_pending = Feedback.query.filter(Feedback.status == 'Pending').count()

    return render_template('feedbacks.html', feedback=feedback, user_feedback_count=user_total_feedback_count, user_total_pending=user_total_pending, total_pending=total_pending)

@main.route('/feedback-archive', methods=['GET', 'POST'])
@login_required
def feedbacks_archive():
    feedback = Feedback.query.filter(Feedback.status == 'Resolved').order_by(Feedback.date_added.desc()).all()

    user_total_feedback_count = Feedback.query.filter(current_user.id == Feedback.user_id).count()
    user_total_pending = Feedback.query.filter(current_user.id == Feedback.user_id, Feedback.status == 'Pending').count()

    return render_template('feedbacks-archive.html', feedback=feedback, user_feedback_count=user_total_feedback_count, user_total_pending=user_total_pending)

@main.route('/links')
@login_required
def links():
    links = Link.query.order_by(Link.is_pinned.desc(), Link.date_added.desc()).all()

    current_user.last_viewed_links = datetime.now(timezone.utc)
    db.session.commit()

    return render_template('links.html', links=links, is_dedicated_page=True)

@main.route('/notifications')
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

@main.route('/profile')
@login_required
def profile():
    form = LoginForm()

    # 1. Grab the key from your .env file
    # (Assuming you are using python-dotenv)
    push_public_key = os.environ.get("VAPID_PUBLIC_KEY")

    # Create a dynamic list to pass to the HTML
    earned_badges = check_earned_badges(current_user.id)
    
    return render_template('profile.html', earned_badges=earned_badges, form=form, vapid_public_key=push_public_key)

@main.route('/class-summaries/<int:id>', methods=['GET', 'POST'])
@login_required
def summary(id):
    # 1. Fetch ALL summaries, ordering by newest date first
    summary = ClassSummary.query.options(joinedload(ClassSummary.course))\
        .get_or_404(id)

    return render_template('summary.html', summary=summary, is_dedicated_page=True, page_title="Class Summary", has_back_btn=True)

@main.route('/class-summaries')
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

    current_user.last_viewed_summaries = datetime.now(timezone.utc)
    db.session.commit()

    return render_template('summaries.html', 
                           grouped_summaries=grouped_summaries, 
                           total_count=total_count,
                           monday=monday, sunday=sunday,
                           req_week=req_week,
                           prev_year=prev_year, prev_week=prev_week,
                           next_year=next_year, next_week=next_week,
                           is_dedicated_page=True, 
                           page_title="Class Summary")

@main.route('/tools/wallpaper')
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

# --- FORM NEW ENTRIES ---
@main.route('/add-entry/announcement', methods=['GET', 'POST'])
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

        return redirect(url_for('main.announcements'))

    return render_template('add-announcement.html', form=form, has_back_btn=True, is_entry=True)

@main.route('/add-entry/course', methods=['GET', 'POST'])
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
        
        try:
            db.session.commit()
            
            # Push Notifications
            all_subscriptions = PushSubscription.query.all()
            for sub in all_subscriptions:
                sub_dict = sub.get_subscription_dict()
                status = send_web_push(
                    subscription_dict=sub_dict, 
                    notification_title="New Class Course!", 
                    notification_body=new_course.title,
                    target_url=f"/courses#course-{new_course.id}"
                )
                if status == "expired":
                    db.session.delete(sub)
            db.session.commit()

            return redirect(url_for('main.courses'))
            
        except IntegrityError:
            db.session.rollback()
            form.code.errors.append('This Course Code already exists in the system.')
    
    return render_template('add-course.html', form=form, has_back_btn=True, is_entry=True)

@main.route('/courses/<int:id>/add-schedule', methods=['GET', 'POST'])
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

        return redirect(url_for('main.courses'))

    return render_template('add-course-schedule.html', course=course, form=form, has_back_btn=True, is_entry=True)

@main.route('/add-entry/deadline', methods=['GET', 'POST'])
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

        return redirect(url_for('main.deadlines'))

    return render_template('add-deadline.html', form=form, has_back_btn=True, is_entry=True)

@main.route('/new-entry/feedback', methods=['GET', 'POST'])
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

        return redirect(url_for('main.feedbacks'))
    elif request.method == 'POST':
        # If it's a POST request but validation failed, print the exact reason!
        print("FEEDBACK FORM FAILED:", form.errors)

    return render_template('add-feedback.html', form=form, has_back_btn=True) 

@main.route('/add-entry/class-summary', methods=['GET', 'POST'])
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

        try:
            db.session.commit() # Try to save to the database FIRST
            
            # If successful, send the push notifications!
            all_subscriptions = PushSubscription.query.all()
            for sub in all_subscriptions:
                sub_dict = sub.get_subscription_dict()
                status = send_web_push(
                    subscription_dict=sub_dict, 
                    notification_title="New Class Summary!", 
                    notification_body=new_summary.content,
                    target_url=f"/class-summaries#summary-{new_summary.id}"
                )
                if status == "expired":
                    db.session.delete(sub)
            db.session.commit() # Commit any deleted dead subscriptions

            return redirect(url_for('main.summaries'))
            
        except IntegrityError:
            db.session.rollback() # Undo the crash
            # Inject a custom error directly into the WTForms date field
            form.date_held.errors.append('A summary for this course on this exact date already exists.')
    else:
        print(form.errors)

    current_user.last_viewed_courses = datetime.now(timezone.utc)
    db.session.commit()
    
    return render_template('add-summary.html', form=form, has_back_btn=True, is_entry=True)


# --- FORM UPDATE ENTRIES ---
@main.route('/update-entry/announcement/<int:id>', methods=['GET', 'POST'])
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
        return redirect(url_for('main.announcements'))
        
    elif request.method == 'GET':
        # GET REQUEST: Pre-fill the form fields with the existing database data
        form.title.data = announcement_to_update.title
        form.content.data = announcement_to_update.content
        form.url.data = announcement_to_update.url
    else:
        # If it's a POST but validate_on_submit() failed, print the exact errors to the terminal!
        print("FORM VALIDATION FAILED:", form.errors)

    return render_template('update-announcement.html', form=form, has_back_btn=True, is_entry=True)

@main.route('/update-entry/course/<int:id>', methods=['GET', 'POST'])
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

        try:
            db.session.commit()
            return redirect(url_for('main.courses'))
        except IntegrityError:
            db.session.rollback()
            form.code.errors.append('This Course Code already exists in the system.')
        
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

@main.route('/courses/<int:id>/update-schedule', methods=['GET', 'POST'])
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
        return redirect(url_for('main.courses'))
        
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

@main.route('/update-entry/deadline/<int:id>', methods=['GET', 'POST'])
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
        return redirect(url_for('main.deadlines'))
        
    elif request.method == 'GET':
        # GET REQUEST: Pre-fill the form fields with the existing database data
        form.course.data = deadline_to_update.course_id
        form.description.data = deadline_to_update.description
        form.category.data = deadline_to_update.category
        form.date_given.data = deadline_to_update.date_given  
        form.due_date.data = deadline_to_update.due_date 
        form.status.data = deadline_to_update.status 
        form.note.data = deadline_to_update.note 
    else:
        # If it's a POST but validate_on_submit() failed, print the exact errors to the terminal!
        print("FORM VALIDATION FAILED:", form.errors)

    return render_template('update-deadline.html', form=form, has_back_btn=True, is_entry=True)

@main.route('/update-entry/feedback/<int:id>', methods=['GET', 'POST'])
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
        return redirect(url_for('main.feedbacks'))

    elif request.method == 'GET':
        form.title.data = feedback_to_update.title
        form.category.data = feedback_to_update.category 
        form.message.data = feedback_to_update.message

    else:
        print("FORM VALIDATION FAILED:", form.errors)

    return render_template('update-feedback.html', form=form, has_back_btn=True) 

@main.route('/profile/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    form = ProfileForm()
    tag_form = CreateTagForm()

    tag_count = Tag.query.count()

    # 1. Fetch all tags and store them in a variable
    all_tags = Tag.query.all()
    
    # 2. Use that variable for your choices
    # This fetches all tags and formats them as (id, name) for WTForms
    form.tags.choices = [(tag.id, tag.name) for tag in all_tags]

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
        return redirect(url_for('main.profile'))

    elif request.method == 'GET':
        # PRE-FILL THE FORM when they first load the page
        form.name.data = current_user.name
        form.bio.data = current_user.bio

        # 3. PRE-CHECK THE BOXES THEY ALREADY OWN
        form.tags.data = [tag.id for tag in current_user.tags]
    else:
        print("FORM VALIDATION FAILED:", form.errors)

    return render_template('update-profile.html', form=form, tag_form=tag_form, all_tags=all_tags, tag_count=tag_count, page_title="Profile", has_back_btn=True)

@main.route('/update-entry/class-summary/<int:id>', methods=['GET', 'POST'])
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

        try:
            db.session.commit()
            return redirect(url_for('main.summaries'))
        except IntegrityError:
            db.session.rollback()
            form.date_held.errors.append('Another summary for this course already exists on this date.')
        
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

# --- RENDER ERROR PAGES ---
# Invalid URL
@main.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Internal Server Error
@main.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500
