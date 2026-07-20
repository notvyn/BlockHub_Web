/* =========================================
   UNIVERSAL ENTRY FORM VALIDATOR (GLOBAL)
   ========================================= */
window.initEntryValidation = function(formId, fieldsConfig) {
    const form = document.getElementById(formId);
    if (!form) return;

    const validators = fieldsConfig.map(field => {
        return function() {
            let isValid = true;
            let targetElement = null;
            let applyBoxBorder = false;
            let dynamicMessage = field.message; // Default message

            // A. Logic Check
            if (field.type === 'text') {
                targetElement = document.getElementById(field.id);
                if (targetElement) isValid = targetElement.value.trim() !== '';
            } 
            else if (field.type === 'float') {
                targetElement = document.getElementById(field.id);
                if (targetElement) {
                    const val = targetElement.value.trim();
                    const numVal = parseFloat(val);
                    
                    // Must not be empty, must be a number, finite, AND greater than or equal to 0
                    isValid = val !== '' && !isNaN(numVal) && isFinite(val) && numVal >= 0;
                }
            }
            else if (field.type === 'url') {
                targetElement = document.getElementById(field.id);
                if (targetElement) {
                    const val = targetElement.value.trim();
                    
                    if (field.optional && val === '') {
                        isValid = true; // It's valid if it's optional and left blank!
                    } else if (val === '') {
                        isValid = false; // It's empty, and NOT optional
                        dynamicMessage = field.messageEmpty || field.message;
                    } else {
                        // It has text, so it MUST match the URL pattern
                        const urlPattern = /^(https?:\/\/)/i;
                        isValid = urlPattern.test(val);
                        dynamicMessage = field.messageFormat || field.message;
                    }
                }
            }
            else if (field.type === 'radio') {
                const radios = document.querySelectorAll(`input[name="${field.name}"]`);
                isValid = Array.from(radios).some(radio => radio.checked);
                if (field.containerId) {
                    targetElement = document.getElementById(field.containerId);
                    applyBoxBorder = true; 
                }
            } 
            else if (field.type === 'easymde') {
                isValid = field.instance.value().trim() !== '';
                if (field.instance.element.nextSibling) {
                    targetElement = field.instance.element.nextSibling;
                    applyBoxBorder = true;
                }
            }
            else if (field.type === 'flatpickr') {
                isValid = field.instance.selectedDates.length > 0;
                targetElement = field.instance.altInput || field.instance.input;
            }

            // B. Visual Updates
            const errorDiv = document.getElementById(field.errorId);
            
            if (isValid) {
                if (targetElement) {
                    targetElement.classList.remove('is-invalid', 'is-valid');
                    if (applyBoxBorder) targetElement.classList.remove('border', 'border-danger', 'p-2', 'rounded');
                }
                if (errorDiv) errorDiv.style.display = 'none';
            } else {
                if (targetElement) {
                    targetElement.classList.remove('is-valid');
                    targetElement.classList.add('is-invalid');
                    if (applyBoxBorder) targetElement.classList.add('border', 'border-danger', 'p-2', 'rounded');
                }
                if (errorDiv) {
                    // Use the dynamically selected error message
                    errorDiv.textContent = dynamicMessage;
                    errorDiv.style.display = 'block';
                }
            }
            return isValid;
        };
    });

    // 2. Attach Live Event Listeners
    fieldsConfig.forEach((field, index) => {
        const validateFn = validators[index];
        
        // Ensure 'url' is added to this listener group alongside text and float!
        if (field.type === 'text' || field.type === 'float' || field.type === 'url') {
            const input = document.getElementById(field.id);
            if (input) input.addEventListener('input', validateFn);
        } else if (field.type === 'radio') {
            const radios = document.querySelectorAll(`input[name="${field.name}"]`);
            radios.forEach(radio => radio.addEventListener('change', validateFn));
        } else if (field.type === 'easymde') {
            field.instance.codemirror.on('change', validateFn); 
        } else if (field.type === 'flatpickr') {
            field.instance.config.onChange.push(validateFn);
        }
    });

    // 3. Gatekeeper
    form.addEventListener('submit', function(e) {
        let isFormValid = true;
        validators.forEach(validateFn => {
            if (!validateFn()) isFormValid = false;
        });
        if (!isFormValid) e.preventDefault();
    });
};


document.addEventListener('DOMContentLoaded', function() {

     // 2. The Regex Patterns
    window.globalConfig = {
        emailRegex: /^\d{2}-\d{5}@g\.batstate-u\.edu\.ph$/,
        passRegex: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/
    }

    // Grab the sidebar
    const sidebar = document.querySelector("#sidebar");

    // Grab both possible toggle buttons (desktop and mobile)
    const toggles = document.querySelectorAll("#toggle-btn, #mobile-toggle");

    // Add the click event to any button that exists
    toggles.forEach(btn => {
        btn?.addEventListener("click", function () {
            sidebar.classList.toggle("expand");
        });
    });

    const eyeToggle = document.querySelectorAll('.eye-toggle');

    eyeToggle.forEach(eye => {
        eye.addEventListener('click', function() {
            const parent = this.closest('.input-group');
            const passwordInput = parent.querySelector('.form-control');

            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                this.innerHTML = '<i class="fa-solid fa-eye"></i>';
            }
            else {
                passwordInput.type = 'password';
                this.innerHTML = '<i class="fa-solid fa-eye-slash"></i>';
            }
        });
    });

    // 3. Helper Function to instantly update the UI and Error Text
    window.setValidation = function (inputElement, isValid, errorMessage) {
        // Find the exact error div matching this input's ID
        const errorDiv = document.getElementById('error-' + inputElement.id);
        
        if (isValid) {
            inputElement.classList.remove('is-invalid');
            inputElement.classList.add('is-valid');
            if (errorDiv) errorDiv.textContent = ''; 
        } else {
            inputElement.classList.remove('is-valid');
            inputElement.classList.add('is-invalid');
            // Inject the specific error text
            if (errorDiv) errorDiv.textContent = errorMessage;
        }
    }

    // Handle Mobile Search Expansion
    const mSearchTrigger = document.getElementById('m-search-trigger');
    const mSearchClose = document.getElementById('m-search-close');
    const mSearchOverlay = document.getElementById('m-search-overlay');
    const mSearchInput = mSearchOverlay.querySelector('input');

    mSearchTrigger.addEventListener('click', () => {
        mSearchOverlay.classList.add('active');
        setTimeout(() => mSearchInput.focus(), 300); // Auto-focuses the keyboard
    });

    mSearchClose.addEventListener('click', () => {
        mSearchOverlay.classList.remove('active');
        mSearchInput.value = ''; // Clears the text when closed
    });

    const checkboxes = document.querySelectorAll('.task-checkbox');
    const badge = document.getElementById('deadline-badge');

    // Check if we are on the Archive page
    const isArchivePage = !!document.getElementById('deadline-archive-page-total-count');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const deadlineId = this.getAttribute('data-id');
            const isCompleted = this.checked;
            
            const taskContainer = this.closest('.deadline-item');
            const taskTitle = taskContainer.querySelector('.md-task-title');
            const statusText = taskContainer.querySelector('.status-text');
            
            // Match mobile and desktop checkboxes
            const allCheckboxesForTask = taskContainer.querySelectorAll('.task-checkbox');
            allCheckboxesForTask.forEach(cb => cb.checked = isCompleted);

            // Send the update to Python
            fetch(`/complete-deadline/${deadlineId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ completed: isCompleted })
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    
                    // MAIN DASHBOARD LOGIC: Fade it out and remove it
                    if (!isArchivePage && isCompleted) {
                        taskContainer.style.transition = 'opacity 0.4s ease';
                        taskContainer.style.opacity = '0';
                        setTimeout(() => {
                            taskContainer.classList.remove('d-flex');
                            taskContainer.classList.add('d-none');
                        }, 400);
                    } 
                    // ARCHIVE PAGE LOGIC: Update text and toggle opacity
                    else if (isArchivePage) {
                        if (taskTitle) taskTitle.style.textDecoration = isCompleted ? 'line-through' : 'none';
                        if (statusText) {
                            statusText.textContent = isCompleted ? 'Done' : 'Missed';
                            statusText.className = isCompleted ? 'fw-bold status-text text-success' : 'fw-bold status-text text-danger';
                        }
                        
                        // NEW: Dim the card if it's done, bring it to full brightness if missed
                        taskContainer.style.opacity = isCompleted ? '0.75' : '1';
                    }

                    // Update the red notification badge on the active page
                    if (badge && data.new_total !== undefined) {
                        if (data.new_total > 0) {
                            badge.textContent = data.new_total;
                            badge.style.display = 'inline-block';
                        } else {
                            badge.style.display = 'none'; 
                        }
                    }

                    updateBadges(data.new_total, data.archive_total);
                }
            })
            .catch(error => console.error('Error updating task:', error));
        });
    });

    // const checkboxes = document.querySelectorAll('.task-checkbox');
    // const badge = document.getElementById('deadline-badge');
    const deadlinePageTotal = document.getElementById('deadline-page-total-count');
    // const toastContainer = document.getElementById('toast-container');
    const deadlineArchivePageTotal = document.getElementById('deadline-archive-page-total-count');

    // // NEW: Determine which page the user is currently on by checking which total count exists
    // const isArchivePage = !!deadlineArchivePageTotal;

    // checkboxes.forEach(checkbox => {
    //     checkbox.addEventListener('change', function() {
    //         const deadlineId = this.getAttribute('data-id');
    //         const isCompleted = this.checked;
            
    //         const taskContainer = this.closest('.deadline-item');
    //         const taskTitle = taskContainer.querySelector('.md-task-title');
    //         const statusText = taskContainer.querySelector('.status-text');
            
    //         const allCheckboxesForTask = taskContainer.querySelectorAll('.task-checkbox');
    //         allCheckboxesForTask.forEach(cb => cb.checked = isCompleted);

    //         taskContainer.style.transition = 'all 0.4s ease';
    //         taskContainer.style.overflow = 'hidden';

    //         // NEW LOGIC: Should this card disappear?
    //         // If on Archive Page: hide when UNCHECKED (false). If on Main Page: hide when CHECKED (true).
    //         const shouldHide = isArchivePage ? !isCompleted : isCompleted;

    //         fetch(`/complete-deadline/${deadlineId}`, {
    //             method: 'POST',
    //             headers: { 'Content-Type': 'application/json' },
    //             body: JSON.stringify({ completed: isCompleted })
    //         })
    //         .then(response => response.json())
    //         .then(data => {
    //             if(data.success) {
                    
    //                 // 1. Immediately update the physical text to match the new status
    //                 if (isCompleted) {
    //                     if (taskTitle) taskTitle.style.textDecoration = 'line-through';
    //                     if (statusText) statusText.textContent = 'Done';
    //                 } else {
    //                     if (taskTitle) taskTitle.style.textDecoration = 'none';
    //                     if (statusText) statusText.textContent = 'Upcoming';
    //                 }

    //                 // 2. Do we hide the card and show the toast?
    //                 if (shouldHide) {
                        
    //                     taskContainer.style.opacity = '0';
                        
    //                     setTimeout(() => {
    //                         taskContainer.classList.remove('d-flex');
    //                         taskContainer.classList.add('d-none');
    //                     }, 400);

    //                     // BUILD THE DYNAMIC STACKING TOAST
    //                     const titleText = taskTitle ? taskTitle.textContent.trim() : 'Task';
                        
    //                     // Dynamic Toast Text based on the page
    //                     const actionText = isArchivePage ? 'moved to Upcoming' : 'marked done';
                        
    //                     const toast = document.createElement('div');
    //                     toast.className = 'bg-dark text-white rounded shadow-lg overflow-hidden';
    //                     toast.style.minWidth = '300px';
    //                     toast.style.transform = 'translateY(100%)';
    //                     toast.style.opacity = '0';
    //                     toast.style.transition = 'transform 0.3s ease, opacity 0.3s ease';

    //                     toast.innerHTML = `
    //                         <div class="p-3 d-flex justify-content-between align-items-center">
    //                             <div class="pe-3">
    //                                 <i class="fa-solid fa-circle-check text-success me-2"></i>
    //                                 <span style="font-size: 0.9rem;"><strong>${titleText}</strong> ${actionText}.</span>
    //                             </div>
    //                             <button class="btn btn-sm btn-outline-light undo-btn" style="font-weight: 600;">UNDO</button>
    //                         </div>
    //                         <div style="height: 4px; background: rgba(255,255,255,0.2);">
    //                             <div class="undo-progress" style="height: 100%; width: 100%; background: var(--accent-purple, #8e44ad);"></div>
    //                         </div>
    //                     `;

    //                     toastContainer.appendChild(toast);
                        
    //                     void toast.offsetWidth;
    //                     toast.style.transform = 'translateY(0)';
    //                     toast.style.opacity = '1';

    //                     const progress = toast.querySelector('.undo-progress');
    //                     setTimeout(() => {
    //                         progress.style.transition = 'width 5s linear';
    //                         progress.style.width = '0%';
    //                     }, 50);

    //                     // 4. The 5-Second Deletion Timer
    //                     const undoTimer = setTimeout(() => {
    //                         toast.style.opacity = '0';
    //                         toast.style.transform = 'translateY(20px)';
    //                         setTimeout(() => toast.remove(), 300);
    //                     }, 5000);

    //                     // 5. The UNDO Button Logic
    //                     toast.querySelector('.undo-btn').addEventListener('click', function() {
    //                         clearTimeout(undoTimer); 
                            
    //                         toast.style.opacity = '0';
    //                         setTimeout(() => toast.remove(), 300);

    //                         // We send the OPPOSITE of what it currently is to undo the action
    //                         const undoState = !isCompleted;

    //                         fetch(`/complete-deadline/${deadlineId}`, {
    //                             method: 'POST',
    //                             headers: { 'Content-Type': 'application/json' },
    //                             body: JSON.stringify({ completed: undoState })
    //                         })
    //                         .then(response => response.json())
    //                         .then(data => {
    //                             if(data.success) {
    //                                 allCheckboxesForTask.forEach(cb => cb.checked = undoState);
    //                                 restoreCard(taskContainer, taskTitle, statusText, undoState);
    //                                 updateBadges(data.new_total, data.archive_total);
    //                             }
    //                         });
    //                     });

    //                 } else {
    //                     // User manually un-did their action before the toast timer ended without using the button
    //                     restoreCard(taskContainer, taskTitle, statusText, isCompleted);
    //                 }
                    
    //                 updateBadges(data.new_total, data.archive_total);
    //             }
    //         })
    //         .catch(error => console.error('Error updating task:', error));
    //     });
    // });

    // // Helper function to restore a crushed card perfectly
    // // Added 'isCompleted' parameter so it knows whether to restore a crossed-out title or a normal one
    // function restoreCard(container, title, status, isCompleted) {
    //     if (title) title.style.textDecoration = isCompleted ? 'line-through' : 'none';
    //     if (status) status.textContent = isCompleted ? 'Done' : 'Upcoming';
        
    //     container.classList.remove('d-none');
    //     container.classList.add('d-flex');
        
    //     container.style.opacity = '1';
    // }

    // Helper function to update the red numbers smoothly
    // Added 'archiveTotal' to smoothly update the number on the Archive page
    function updateBadges(newTotal, archiveTotal) {
        if (badge && newTotal !== undefined) {
            if (newTotal > 0) {
                badge.textContent = newTotal;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none'; 
            }
        }
        
        if (deadlinePageTotal && newTotal !== undefined) {
            deadlinePageTotal.style.opacity = '0';
            setTimeout(() => {
                deadlinePageTotal.textContent = newTotal;
                deadlinePageTotal.style.opacity = '1';
            }, 150);
        }

        if (deadlineArchivePageTotal && archiveTotal !== undefined) {
            deadlineArchivePageTotal.style.opacity = '0';
            setTimeout(() => {
                deadlineArchivePageTotal.textContent = archiveTotal;
                deadlineArchivePageTotal.style.opacity = '1';
            }, 150);
        }
    }
    
    // Grab all our new filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    // Grab all the task containers
    const deadlines = document.querySelectorAll('.deadline-item');

    filterButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault(); // Stops the page from jumping to the top when clicking an '#' link
            
            // What filter did they click? (urgent, week, or all)
            const filterType = this.getAttribute('data-filter');

            // Visual Update: Make only the clicked button bold
            filterButtons.forEach(b => b.classList.remove('fw-bold'));
            this.classList.add('fw-bold');

            // Loop through every task on the screen
            deadlines.forEach(item => {
                // Grab the invisible days_left number we injected
                const days = parseInt(item.getAttribute('data-days'));
                const thisWeek = item.getAttribute('data-this-week'); // Grab our new boolean string
                let shouldShow = false;

                // The Logic Rules
                if (filterType === 'all') {
                    shouldShow = true;
                } else if (filterType === 'urgent' && days <= 2) { // Matches your md-code-hot threshold
                    shouldShow = true;
                } else if (filterType === 'week' && thisWeek === 'true') {
                    shouldShow = true;
                }

                // Instantly hide or show the task
                // (Using 'flex' because your .md-task class uses display: flex)
                item.style.display = shouldShow ? 'flex' : 'none'; 
            });
            
            // Optional: You could add logic here to make the clicked link bold or change color!
            item.style.backgroundColor = 'purple';
        });

        // 1. Setup: Grab authentication status from the container
        const container = document.getElementById('dashboard-container');
        const isLoggedIn = container.getAttribute('data-logged-in') === 'true';
        
        if (!isLoggedIn) {
            // ... (Your existing Guest Memory Check code stays exactly the same) ...
            let guestReadIds = JSON.parse(localStorage.getItem('guestReadAnnouncements')) || [];
            document.querySelectorAll('.new-tag').forEach(tag => {
                let tagId = tag.id.split('-')[1]; 
                if (guestReadIds.includes(tagId)) { tag.style.display = 'none'; }
            });
        } else {
            // NEW LOGIC: The user is logged in! Let's check for guest data to sync.
            let guestReadIds = JSON.parse(localStorage.getItem('guestReadAnnouncements'));
            
            // If there is data to sync...
            if (guestReadIds && guestReadIds.length > 0) {
                
                // 1. Instantly hide the tags on the screen for a smooth UX
                guestReadIds.forEach(id => {
                    const tag = document.getElementById(`tag-${id}`);
                    if (tag) tag.style.display = 'none';
                });
                
                // 2. Send the data to our new Python route
                fetch('/sync-guest-reads', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ ids: guestReadIds })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // 3. The server saved them safely. Delete the local browser memory!
                        localStorage.removeItem('guestReadAnnouncements');
                    }
                })
                .catch(error => console.error('Error syncing data:', error));
            }
        }

        /* =========================================
            DYNAMIC BADGE COUNTER
            ========================================= */
        function updateAnnouncementBadge() {
            const badge = document.getElementById('announcement-badge');
            let unreadCount = 0;

            // Loop through all the "NEW" tags on the page
            document.querySelectorAll('.new-tag').forEach(tag => {
                // If the tag is NOT hidden, it means it's unread!
                if (tag.style.display !== 'none') {
                    unreadCount++;
                }
            });

            // Update the badge UI
            if (unreadCount > 0) {
                badge.textContent = unreadCount;
                badge.style.display = 'inline-block'; // Show it
            } else {
                badge.style.display = 'none'; // Hide it if 0
            }
        }

        // 1. Run the counter immediately when the page loads
        updateAnnouncementBadge();

        // 3. The Click Event
        document.querySelectorAll('.announcement-link').forEach(link => {
            link.addEventListener('click', function() {
                const announcementId = this.getAttribute('data-id');
                const tag = document.getElementById(`tag-${announcementId}`);
                
                if (tag && tag.style.display !== 'none') {
                    // Visually hide it instantly for EVERYONE
                    tag.style.display = 'none';

                    // Run the counter again to decrease the badge number instantly!
                    updateAnnouncementBadge();
                    
                    if (isLoggedIn) {
                        // LOGGED IN: Tell the Python server to save it to the database
                        fetch(`/mark-announcement-read/${announcementId}`, {
                            method: 'POST'
                        }).catch(error => console.error('Database error:', error));
                    } else {
                        // GUEST: Save it to the browser's local memory instead
                        let guestReadIds = JSON.parse(localStorage.getItem('guestReadAnnouncements')) || [];
                        
                        // Add the new ID to the list if it isn't already there
                        if (!guestReadIds.includes(announcementId)) {
                            guestReadIds.push(announcementId);
                            // Save the updated list back to the browser
                            localStorage.setItem('guestReadAnnouncements', JSON.stringify(guestReadIds));
                        }
                    }
                }
            });
        });  
    });

    /* =========================================
       UNIFIED DARK MODE CONTROLLER
       ========================================= */
    const themeToggleBtns = document.querySelectorAll('.theme-toggle-btn');
    const settingsDarkModeToggle = document.getElementById('settingsDarkMode');

    // 1. The Master Function that changes everything at once
    function applyTheme(isDark) {
        // Change the actual CSS theme and save it
        if (isDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('blockhub_theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('blockhub_theme', 'light');
        }

        // Sync the Header Icons (Sun/Moon)
        themeToggleBtns.forEach(btn => {
            btn.innerHTML = isDark ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
        });

        // Sync the Settings Toggle Switch (if they are on the profile page)
        if (settingsDarkModeToggle) {
            settingsDarkModeToggle.checked = isDark;
        }
    }

    // 2. Initialize on Page Load (Read the saved memory)
    const savedTheme = localStorage.getItem('blockhub_theme');
    const isCurrentlyDark = (savedTheme === 'dark');
    applyTheme(isCurrentlyDark);

    // 3. Click Event for the Header Button (Sun/Moon Icon)
    themeToggleBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            // Check current state and send the OPPOSITE to the master function
            const currentlyDark = document.documentElement.getAttribute('data-theme') === 'dark';
            applyTheme(!currentlyDark); 
        });
    });

    // 4. Click Event for the Settings Tab Switch
    if (settingsDarkModeToggle) {
        settingsDarkModeToggle.addEventListener('change', function() {
            // Send the exact state of the switch (true/false) to the master function
            applyTheme(this.checked); 
        });
    }

    /* =========================================
    UNIFIED MODAL AJAX SUBMISSION (ADD & UPDATE)
    ========================================= */
    const linkModal = document.getElementById('addLinkModal');
    const linkForm = document.getElementById('addLinkForm');

    if (linkModal) {
        // 1. SHAPESHIFT THE MODAL WHEN IT OPENS
        linkModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            
            // Check if we are adding or editing (default to add if no attribute exists)
            const mode = button.getAttribute('data-mode') || 'add';
            
            const modalTitle = linkModal.querySelector('.modal-title');
            const titleInput = document.getElementById('title');
            const urlInput = document.getElementById('url');
            
            // Hide any lingering error messages
            document.getElementById('title-error').style.display = 'none';
            document.getElementById('url-error').style.display = 'none';

            if (mode === 'edit') {
                // Transform into an UPDATE modal
                modalTitle.textContent = 'Update Quick Link';
                titleInput.value = button.getAttribute('data-title');
                urlInput.value = button.getAttribute('data-url');
                
                // Tell the form it is in edit mode and give it the specific ID
                linkForm.setAttribute('data-form-mode', 'edit');
                linkForm.setAttribute('data-target-id', button.getAttribute('data-id'));
            } else {
                // Transform into an ADD modal
                modalTitle.textContent = 'Add Quick Link';
                linkForm.reset(); // Clear the text boxes
                
                // Tell the form it is in add mode
                linkForm.setAttribute('data-form-mode', 'add');
                linkForm.removeAttribute('data-target-id');
            }
        });
    }

    if (linkForm) {
        // 2. HANDLE THE FORM SUBMISSION
        linkForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Stop page reload
            
            document.getElementById('title-error').style.display = 'none';
            document.getElementById('url-error').style.display = 'none';
            
            const formData = new FormData(this);
            const mode = this.getAttribute('data-form-mode');
            
            // Dynamically set the correct Python route based on the mode
            let fetchUrl = '/api/add-link';
            if (mode === 'edit') {
                const targetId = this.getAttribute('data-target-id');
                fetchUrl = `/api/update-link/${targetId}`;
            }
            
            fetch(fetchUrl, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // The easiest way to show the new/updated data is a clean reload
                    window.location.reload();
                } else {
                    // Show errors
                    if (data.errors.title) {
                        const err = document.getElementById('title-error');
                        err.textContent = data.errors.title[0];
                        err.style.display = 'block';
                    }
                    if (data.errors.url) {
                        const err = document.getElementById('url-error');
                        err.textContent = data.errors.url[0];
                        err.style.display = 'block';
                    }
                }
            })
            .catch(error => console.error('Fetch error:', error));
        });
    }

    /* =========================================
       9. LIVE FORM VALIDATION (QUICK LINKS)
       ========================================= */
    const titleInput = document.getElementById('title');
    const urlInput = document.getElementById('url');
    const titleError = document.getElementById('title-error');
    const urlError = document.getElementById('url-error');

    function isValidURL(string) {
        const urlPattern = /^(https?:\/\/)/i;
        return urlPattern.test(string);
    }

    // TITLE FIELD LOGIC
    if (titleInput && titleError) {
        titleInput.addEventListener('input', function() {
            if (this.value.trim() === '') {
                // Invalid State
                titleError.textContent = 'Please provide a title for the link.';
                titleError.style.display = 'block';
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            } else {
                // Success State!
                titleError.style.display = 'none';
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    }

    // URL FIELD LOGIC
    if (urlInput && urlError) {
        urlInput.addEventListener('input', function() {
            if (this.value.trim() === '') {
                // Invalid State (Empty)
                urlError.textContent = 'Please provide a URL.';
                urlError.style.display = 'block';
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            } else if (!isValidURL(this.value)) {
                // Invalid State (Bad Format)
                urlError.textContent = 'URL must start with http:// or https://';
                urlError.style.display = 'block';
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            } else {
                // Success State!
                urlError.style.display = 'none';
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    }

    /* =========================================
       10. MODAL CLEANUP ROUTINE
       ========================================= */
    const addLinkModal = document.getElementById('addLinkModal');
    
    // Create a reusable function to scrub everything clean
    function scrubLinkForm() {
        const form = document.getElementById('addLinkForm');
        if (form) form.reset(); // 1. Clear the text
        
        // 2. Hide the error messages
        const tError = document.getElementById('title-error');
        const uError = document.getElementById('url-error');
        if (tError) tError.style.display = 'none';
        if (uError) uError.style.display = 'none';
        
        // 3. Strip away all the green/red validation glows
        const inputs = form.querySelectorAll('.form-control');
        inputs.forEach(input => {
            input.classList.remove('is-valid', 'is-invalid');
        });
    }

    // Tell Bootstrap to run our scrub function every time the modal closes
    if (addLinkModal) {
        addLinkModal.addEventListener('hidden.bs.modal', function () {
            scrubLinkForm();
        });
    }

    document.querySelectorAll('.heart-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const announcementId = this.getAttribute('data-id');
            const icon = this.querySelector('.heart-icon');
            const countSpan = this.querySelector('.heart-count');

            fetch(`/toggle-heart/${announcementId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the total number
                    countSpan.textContent = data.total_hearts;
                    
                    // Toggle the icon style between filled (solid red) and empty (regular)
                    if (data.is_hearted) {
                        icon.classList.remove('fa-regular');
                        icon.classList.add('fa-solid', 'text-danger'); 
                    } else {
                        icon.classList.remove('fa-solid', 'text-danger');
                        icon.classList.add('fa-regular');
                    }
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });

    // 1. Target every single link specifically inside the announcement content
    const contentLinks = document.querySelectorAll('.card-content a');
    
    contentLinks.forEach(link => {
        // 2. Force the link to open in a new tab
        link.setAttribute('target', '_blank');
        
        // 3. Security best practice: Prevents the new tab from maliciously hijacking your dashboard page
        link.setAttribute('rel', 'noopener noreferrer');
    });
    

    // 1. Target the elements
    const courseRadios = document.querySelectorAll('.course-radio');
    const scheduleContainer = document.getElementById('dynamic-date-container');
    
    // 2. Listen for clicks on ANY course radio button
    courseRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const selectedCourseId = this.value;
            
            scheduleContainer.innerHTML = '<span class="text-muted" style="font-size: 0.85rem; font-style: italic;">Loading schedules...</span>';
            
            fetch(`/api/get-schedules/${selectedCourseId}`)
                .then(response => response.json())
                .then(data => {
                    scheduleContainer.innerHTML = '';
                    
                    if (data.schedules.length === 0) {
                        scheduleContainer.innerHTML = '<span class="text-danger fw-bold" style="font-size: 0.85rem;">No schedules found for this course.</span>';
                        return;
                    }

                    // NEW: Grab the hidden saved ID from the HTML
                    const savedScheduleId = scheduleContainer.getAttribute('data-saved-schedule');
                    
                    data.schedules.forEach(sched => {
                        // NEW: If the current loop matches the saved ID, add the 'checked' attribute
                        const isChecked = (savedScheduleId == sched.id) ? 'checked' : '';
                        
                        const htmlString = `
                            <input class="btn-check" id="schedule-${sched.id}" name="schedule" required type="radio" value="${sched.id}" ${isChecked}>
                            <label class="btn-pill" for="schedule-${sched.id}">${sched.label}</label>
                        `;
                        scheduleContainer.insertAdjacentHTML('beforeend', htmlString);
                    });
                })
                .catch(error => console.error('Error fetching schedules:', error));
        });
    });

    // NEW: Auto-trigger the loading process when the page first opens!
    // If WTForms pre-selected a course, we simulate a click on it so the schedules load instantly.
    const preSelectedCourse = document.querySelector('.course-radio:checked');
    if (preSelectedCourse) {
        preSelectedCourse.dispatchEvent(new Event('change'));
    }
    
    // 2. Listen for any clicks inside this container
    if (scheduleContainer) {
        scheduleContainer.addEventListener('change', function(e) {
            
            // 3. Ensure they actually clicked a radio button
            if (e.target && e.target.matches('input[name="schedule"]')) {
                
                // 4. Find the label attached to this radio button and read its text
                const labelText = document.querySelector(`label[for="${e.target.id}"]`).innerText;
                
                // Extract just the day part (e.g., splits "Monday | 07:00 AM" and grabs "Monday")
                const selectedDayString = labelText.split('|')[0].trim(); 
                
                // 5. Map the text string to JavaScript's numbered days (0 = Sunday, 1 = Monday)
                const daysOfWeek = {
                    'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 
                    'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6
                };
                
                const targetDayNum = daysOfWeek[selectedDayString];
                
                if (targetDayNum !== undefined) {
                    const today = new Date();
                    const currentDayNum = today.getDay();
                    
                    // 6. Calculate the math to find the most recent occurrence of that day
                    let daysToSubtract = currentDayNum - targetDayNum;
                    
                    // If the target day is ahead of us in the week (e.g., today is Tuesday(2), target is Friday(5)),
                    // we need to wrap around to the previous week's Friday.
                    if (daysToSubtract < 0) {
                        daysToSubtract += 7; 
                    }
                    
                    // 7. Calculate the exact historical date
                    const targetDate = new Date(today);
                    targetDate.setDate(today.getDate() - daysToSubtract);
                    
                    // 8. Command Flatpickr to jump to this new date instantly!
                    fpInstance.setDate(targetDate);
                }
            }
        });
    }

    // 1. Grab the inputs
    const nameInput = document.getElementById('name')
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirm_password');

    // --- NAME VALIDATION ---
    if (nameInput) {
        nameInput.addEventListener('input', function() {
            const isValid = this.value !== '';
            window.setValidation(this, isValid, 'Please enter a valid name');
        });
    }

    // --- EMAIL VALIDATION ---
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const isValid = window.globalConfig.emailRegex.test(this.value);
            window.setValidation(this, isValid, 'Format: 25-00000@g.batstate-u.edu.ph');
        });
    }

    // --- PASSWORD VALIDATION ---
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const isValid = window.globalConfig.passRegex.test(this.value);
            window.setValidation(this, isValid, 'Min 8 chars, 1 uppercase, 1 lowercase, 1 number.');
            
            // If they fix the main password, force the confirm box to re-check itself
            if (confirmInput.value) {
                confirmInput.dispatchEvent(new Event('input'));
            }
        });
    }

    // --- CONFIRM PASSWORD VALIDATION ---
    if (confirmInput) {
        confirmInput.addEventListener('input', function() {
            // Fix: It must match exactly AND the main password must actually be strong!
            const isMatch = this.value === passwordInput.value && this.value !== '';
            const isMainValid = window.globalConfig.passRegex.test(passwordInput.value);
            
            window.setValidation(this, (isMatch && isMainValid), 'Passwords do not match or main password is weak.');
        });
    }
});
