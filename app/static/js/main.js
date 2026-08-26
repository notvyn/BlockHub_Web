import {getReadHistory, initAnnouncementForm, readAnnouncement, setFileIcon, toggleAnnouncementPin, toggleHeartReact, toggleLightboxModal, updateAnnouncementBadge} from './announcements.js';
import {eyeToggle, validateSignUpInput} from './auth.js';
import {toggleDarkMode, toggleDeleteEntry, toggleLiveSearch, toggleMobileSearchBar, toggleSearchHighlight, toggleSidebarExpand} from './core.js';
import {initCourseForm, initCoursePage, toggleCourseSyllabusModal, toggleMasterCalendar} from './courses.js';
import {initOnboardingTour} from './dashboard.js';
import {completeDeadline, filterDeadline, initDeadlineForm} from './deadlines.js';
import {initFeedbackForm, resolveFeedback, toggleFeedbackReplyModal} from './feedbacks.js';
import {cleanInputLinkModal, toggleLinkModal, toggleLinkPin, validateLinkForm} from './links.js';
import {initScheduleForm} from './schedules.js';
import {getCourseRadios, initSummaryForm} from './summaries.js';
import {initTourReset, initUpdateProfileSettings, toggleCreateTag, toggleNotificationSubscription, toggleUserProfileUpdate} from './profile.js';
import {setAnchorToAnnouncement} from './utils.js';
import {initWallpaperGenerator} from './wallpaper.js';

document.addEventListener('DOMContentLoaded', function() {
    // Authentication Features (logged out)
    eyeToggle();
    validateSignUpInput();

    // Global Features 
    toggleDarkMode();
    toggleLiveSearch();
    toggleMobileSearchBar();
    toggleSearchHighlight();
    toggleSidebarExpand();

    toggleDeleteEntry();
    
    // Announcement Features
    getReadHistory(); // Has Errors in it, I think
    initAnnouncementForm();
    readAnnouncement();
    setFileIcon();
    toggleAnnouncementPin();
    toggleHeartReact();
    toggleLightboxModal();
    updateAnnouncementBadge();

    // Course Features
    initCourseForm();
    initCoursePage();
    toggleCourseSyllabusModal();
    toggleMasterCalendar();

    // Dashboard Features
    initOnboardingTour();

    // Deadline Features
    completeDeadline();
    filterDeadline();
    initDeadlineForm();

    // Feedback Features
    initFeedbackForm();
    resolveFeedback();
    toggleFeedbackReplyModal();

    // Link Features
    cleanInputLinkModal();
    toggleLinkModal();
    toggleLinkPin();
    validateLinkForm();

    // Schedules Features
    initScheduleForm();

    // Summary Features
    getCourseRadios();
    initSummaryForm();

    // Profile Features
    initTourReset();
    initUpdateProfileSettings();
    toggleCreateTag();
    toggleNotificationSubscription();
    toggleUserProfileUpdate();

    // Utilities 
    setAnchorToAnnouncement();

    // Wallpaper Features
    initWallpaperGenerator();
});