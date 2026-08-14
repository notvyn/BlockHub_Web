# KomSy3 (formerly BlockHub_Web) - UNDER DEVELOPMENT
A centralized class management system for CS 2103.

**Created By: John Calvin Samson**

## DOCUMENTATION
**Jul 7, 2026**
- Updated Dashboard Content to show newly added contents.
- Modified `model.py` & `webforms.py` to include properties for Announcement, ClassSummary, Course, Deadline, Link, and User.
- Drafted templates for adding entries (i.e Announcement, Course, Deadline, Link, Summary, Login, Signup)
- Enabled Login, Signup and Logout feature

**July 8, 2026**
- Modified Dashboard navigation redirection to individual pages.
- Enhanced UX through deadline task filters, responsive interaction tags (i.e. "new"), and
- Fixed duplicated cards of the same course in the Latest Summary Section.
- Updated sidebar navigation (i.e. made Site logo redirect to dashboard).
- Limited the visible content for Announcement, and refined UX through clickable titles.
- Created AnnouncementRead model for tagging unread announcements.

<p align="center">
    <img src="app/assets/july-08-2026-d1.png" alt="July 08, 2026 - Enhanced Dashboard UI & UX" width="45%">
    <img src="app/assets/july-08-2026-d2.png" alt="July 08, 2026 - Hover Effect & Mark Task" width="45%">
</p>

**July 9, 2026**
- Enabled routing for viewing individual announcement.
- Enabled Dark Mode for Dashboard Content.
- Fixed checkbox logic to properly remove task once clicked.
- Created Dropdown for creating entries
- Drafted Announcement Posting Page (has visual bugs)

**July 10, 2026**
- Fixed Announcement Posting Page visual bug.
- Changed mobile navbar design to put search, theme, and add button at the top.
- Organized css files for better styling accessibility.
- Created Summary, Deadline, and Course Form Page
- Drafted dedicated pages of each content

**July 11, 2026**
- Added overdue tag for deadline task 
- Added image upload feature using cloudinary, reaction button, and seen by count
- Fixed Announcements page and Enabled editing and deleting of post.
- Created URL pattern validator and constructed element validator for potential cross site scripting (XSS) attacks
- Enable image and file uploading
- Made it so the back button redirects back to previous page (based on site history)
- Separated modals into a single html file

**July 12, 2026** 
- Styled Deadlines Page
- Enabled Edit and Delete feature on Deadline Page

**July 13, 2026**
- Refined positioning of Deadline Page Cards
- Fixed deadline task checkbox interaction
- Added undo button for marking task as done
- Created deadlines-archive page and refined task status update logic 

**July 14, 2026**
- Aligned Course Page styling
- Added delete logic for orphans of relational database model
- Enabled edit and delete feature of both course and schedule
- Added a master schedule accordion above course card, and a total units
- Added instructor email and mailto href value
- Added room to CourseSchedule model
- Fixed updating of total units

**July 15, 2026**
- Fixed ClassSummary page query
- Fixed Add Summary Forms
- Enabled Read more feature on ClassSummary Page
- Added Pagination for ClassSummary Page
- Added Links page
- Enabled Edit and Delete Feature of Links Page
- Refined logic of LinkForm Modal

**July 16, 2026**
- Enabled Search Feature for mobile and desktop
- Created Service workers for site notification

**July 17, 2026**
- Created Notification page for viewing recently added
- Created Feedback page
- Drafted Profile and Account Settings
- Drafted Blockmates page
- Added Email change validation and Password hashing

**July 18, 2026**
- Styled Login and Signup Page
- Added validation form (i.e. Password and Email Matching)
- Refined query logic for Deadlines 
- Fixed Cascading attribute of relational models
- Changed logout sidebar icon
- Added password toggle on authentication pages
- Refine resolve feature on Feedback page

**July 19, 2026**
- Drafted Wallpaper Generator page
- Added tools for sidebar (needs refinement)
- Added description key for Earned badges
- Refined styling of profile page

**July 20, 2026**
- Added Form validation for Profile Security Forms
- Added Form validation to Add Entry pages and Update Entry pages (i.e. Announcement, Summary, Course, Feedback, Schedule)
- Added role badge and admin badge to profile, blockmates, and blockmate page 
- Added conditional display of having no content for pages
- Created feedbacks archive template for resolved items
- Created error page handlers
- Fixed light blinking dark mode 
- Fixed Wallpaper Page and Template 1, added card and background opacity bar

**July 21, 2026**
- Created two more templates for Wallpaper Generator
- Refined styling of wallpaper generator
- Fixed tools navbar
- Fixed Feedbacks' action buttons positioning
- Refined update profile styling and tag creation logic

**July 22, 2026**
- Created Feedback page and added view post on Feedbacks
- Fixed edit mode of tag creation modal
- Updated back button url 
- Added pin feature for announcements and changed action button UI to dropdown
- Fixed update_deadline date route issue
- Fixed sidebar two layer tool navigation and badge/dot display
- Fixed announcement page mark as read issue
- Refined Dashboard Announcement Section query (Unread vs Recently added) limited to only 3
- Changed read by to users' profile image 

**July 23, 2026**
- Created new badges
- Added unique constraint to ClassSummary models and added error catching
- Added pin feature on links
- Added individual read entry on dashboard announcement and summary section
- Refined Tags by making it each category collapsible, has tag limitation, and sliced user tags for visual clarity
- Restyled lightbox modal and files uploaded in easymde content
- Updated file uploaded icons
- Fixed mobile sidebar footer issue
- Added two slider (zoom and card position) on Wallpapers
- Fixed hover effect of dropdown delete button

**July 24, 2026 **
- Truncated super lengthy course title on Dashboard
- Fixed phone download not going through (wallpaper page)
- Fixed styling login email focus style issue 
- Refined Announcement url entry validation
- Refactored/Restructured Routing to three classification (api, auth, main)
- Refined validation of Feedback pending/resolve page
- Partially organized and restructured javascript folder

**July 25, 2026**
- Finished organizing javascript folder
- Added conditional text on dashboard filters
- Changed This Week filter to Next 7 Days
- Fixed sidebar profile picture issue
- Cleaned the css folder
- Added role validation on edit and delete buttons (course & deadline)

**August 2, 2026**
- Fixed dashboard deadline empty message

**August 11, 2026**
- Fixed cloudinary issue on hosting site by adding an internal port

**August 12, 2026**
- Fixed schedule snapping to nearest date when adding summaries 
- Fixed visual issue of links three dot - other link's dots are showing
- Refined documentation and renamed it to milestone

**August 13, 2026**
- Refined file comments

**August 14, 2026**
- Added Schedule Manager for wallpaper generator
- Added custom schedule importer on wallpaper generator
- Added import course and schedule on courses page
- Added email verification on sign up
- Ensure that only one flash message is shown on login page
- Added restriction on dashboard links
- Added landing page and made wallpaper generator public
- Fixed day sorting on wallpaper generator import
- Refine description of Landing page
- Added "check spam" text for new users
- Refine responsiveness of preview content on wallpaper generator
- Refine styling of profile forms (i.e. updateEmail, updatePassword, and deleteIcon)
- Refine extra header style on courses page
- Refine margin of landing page contents

## TO-DO LIST
- [/] Avoid duplicates for Class Summary Sections.
- [/] Add password security and form validation. (Added form validation to Profile, Announcement, Course, Deadline, Summary, Feedback)
- [/] Limit content for Announcement.
- [/] Enable Dark Mode.
- [/] Enable dropdown for adding entry.
- [/] Build Search Feature.
- [/] Construct Templates for entries.
- [/] Create route for individual viewing of announcement
- [/] Fix total deadline visual number
- [/] Fix style and structure dedicated pages for each content (i.e. Announcement ✔️, Courses✔️, Deadlines✔️, Summaries✔️)
- [/] Create new model for Courses' schedule
- [/] Include total number of content and other labels on each dedicated pages
- [/] Add small red dot on sidebar for pages with new content
- [/] Fix Recent Announcements Total Count and refine Query (Dashboard) 
- [/] Have a live update on the total content count for each action on a page
- [/] Fix mobile sidebar screen UI issue 
- [/] Fix Total Units live update count
- [/] Have conditional text for no entry pages (Summaries and Deadlines already done, added archives, links, announcements, courses)
- [/] Add Room to the Master Schedule and Model
- [/] Fix total count badge of deadline on dashboard
- [/] Refine logic of Announcement query on dashboard
- [ ] Refine styling of dashboard
- [/] Refine Styling of Notification, Feedback, Profile, Login, Signup, and Blockmates (Login and Signup done)
- [/] Create list of badges for profiles
- [/] Create new model for each user completion of Task
- [/] Add is_pinned on Announcements and Links
- [/] Fix styling of Wallpaper Generator
- [/] Create two more templates for Wallpaper generator
- [/] Fix Tools sidebar navigation and interaction
- [/] Fix Feedback action buttons positioning
- [/] Fix edit mode of CreateTagModal
- [/] Create a dedicated individual page for feedback entries
- [/] Make each course unique in models
- [/] Fix tag seed initialization.
- [/] Fix date value for editing deadlines
- [/] Fix announcements page mark as read issue
- [/] Fix duplicate entries for summaries
- [/] Add constraint to summaries and deadlines if there's no courses found yet.
- [ ] Fix master schedule no live update
- [/] Fix super lengthy course title
- [/] Fix other phone download not going through (wallpaper page)
- [/] Fix login email focus style issue 
- [/] Fix Announcement url entry validation
- [ ] Create a conditional text for no admin reply in Feedbacks
- [/] Create a conditional text for no urgent task right now or within this week 
- [/] Fix size of sidebar profile pic
- [/] Create a conditional text for no current pending feedback 
- [/] Fix sidebar visual issue when new tag is created 

Known Bugs 
- [ ] Task update element display not in real-time 
- [ ] Deadline Archive Task unchecked marked as missed even if due date is not overdue 

FUTURE VISION
- [ ] Add a GWA Calculator that stores user's scores (w/ accordance to data privacy and the syllabus)
- [ ] Maybe add a grading computation for Course (possibly creation of a dedicated page for each course)