"""(Page Manager) - This is where the magic happens. It connects the URL (e.g., /dashboard) to the right HTML page."""

from flask import render_template, redirect, url_for, request, send_from_directory
from flask_login import current_user, login_required
from sqlalchemy import func, or_, text
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from datetime import date, timedelta, datetime, timezone, time

from app import app, db

import cloudinary
import cloudinary.uploader

from app.models import User, Announcement, AnnouncementRead, AnnouncementHeart, ClassSummary, Course, CourseSchedule, Deadline, Link, PushSubscription, Feedback, Tag, DeadlineCompletion
from app.forms import AnnouncementForm, ClassSummaryForm, CourseForm, CourseScheduleForm, DeadlineForm, LinkForm, LoginForm, SignupForm, FeedbackForm, ProfileForm, CreateTagForm
from app.filters import markdown_filter, parse_links_filter, extract_images_filter, remove_images_filter, time_ago_filter
from app.utils import send_web_push, send_verification_email















































    

















    


