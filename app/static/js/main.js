import {getReadHistory, readAnnouncement, setFileIcon, toggleAnnouncementPin, toggleHeartReact, updateAnnouncementBadge} from './announcements.js';
import {eyeToggle, validateSignUpInput} from './auth.js';
import {toggleDarkMode, toggleMobileSearchBar, toggleSidebarExpand} from './core.js';
import {completeDeadline, filterDeadline} from './deadlines.js';
import {toggleFeedbackReplyModal} from './feedbacks.js';
import {cleanInputLinkModal, toggleLinkModal, validateLinkForm} from './links.js';
import {getCourseRadios} from './summaries.js';
import {setAnchorToAnnouncement} from './utils.js';

document.addEventListener('DOMContentLoaded', function() {
    // Authentication Features (logged out)
    eyeToggle();
    validateSignUpInput();

    // Global Features 
    toggleDarkMode();
    toggleMobileSearchBar();
    toggleSidebarExpand();
    
    // Announcement Features
    // getReadHistory(); // Has Errors in it, I think
    readAnnouncement();
    setFileIcon();
    toggleAnnouncementPin();
    toggleHeartReact();
    updateAnnouncementBadge();

    // Deadline Features
    completeDeadline();
    filterDeadline();

    // Feedback Features
    toggleFeedbackReplyModal();

    // Link Features
    cleanInputLinkModal();
    toggleLinkModal();
    validateLinkForm();

    // Summary Features
    getCourseRadios();

    // Utilities 
    setAnchorToAnnouncement();
});