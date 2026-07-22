document.addEventListener('DOMContentLoaded', function() {
    let itemToDeleteId = null;
    let itemToDeleteType = null;
    let itemCount = null;
    let cardToRemove = null;
    let redirectUrl = null;

    // 1. When ANY trash can button is clicked...
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            // Grab the ID and the new 'data-type' attribute
            itemToDeleteId = this.getAttribute('data-id');
            itemToDeleteType = this.getAttribute('data-type');

            redirectUrl = this.getAttribute('data-redirect');
            
            if (itemToDeleteType !== 'course-schedule') {
                itemCount = this.getAttribute('data-count');
            }
            
            // This targets the specific container. 
            // We include multiple classes here so it works across ALL your different pages!
            cardToRemove = this.closest('.schedule-item, .card-wrapper, .feed-card, .md-task, .split-zone-row');
        });
    });

    // 2. When the "Yes, Delete" button inside ANY global modal is clicked...
    // FIX 1: Use querySelectorAll so we can use .forEach()
    const confirmDeleteBtns = document.querySelectorAll('.confirmDeleteBtn');
    
    if (confirmDeleteBtns.length > 0) {
        confirmDeleteBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // Safety check: Don't do anything if we don't have an ID and a Type
                if (!itemToDeleteId || !itemToDeleteType) return;

                // FIX 2: Find the exact modal this specific button belongs to
                const currentModalElement = this.closest('.modal');

                // Dynamically inject the type and ID into the fetch URL
                fetch(`/delete-entry/${itemToDeleteType}/${itemToDeleteId}`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        
                        // Hide whichever Bootstrap modal we are currently using
                        if (currentModalElement) {
                            const activeModal = bootstrap.Modal.getInstance(currentModalElement);
                            activeModal.hide();
                        }

                        // --- NEW LOGIC: Trigger Redirect ---
                        if (redirectUrl) {
                            window.location.href = redirectUrl;
                            return; // Stop the script here so it doesn't try to animate the old card!
                        }

                        // Smoothly fade out the specific card we clicked
                        if (cardToRemove) {
                            
                            // --- NEW LOGIC: Class Summary Date Group Cleanup ---
                            if (itemToDeleteType === 'class-summary') {
                                // Find the parent group and the bootstrap column wrapper
                                const parentGroup = cardToRemove.closest('.summary-group');
                                const colWrapper = cardToRemove.closest('.col-12') || cardToRemove;
                                
                                if (parentGroup) {
                                    // Count how many cards are currently inside this specific date block
                                    const cardsInGroup = parentGroup.querySelectorAll('.card-wrapper').length;
                                    
                                    if (cardsInGroup <= 1) {
                                        // If it's 1, this is the very last card! Fade out the entire date group.
                                        parentGroup.style.transition = 'opacity 0.4s ease';
                                        parentGroup.style.opacity = '0';
                                        setTimeout(() => parentGroup.remove(), 400);
                                    } else {
                                        // If there are other cards left, just remove this specific column
                                        colWrapper.style.transition = 'opacity 0.4s ease';
                                        colWrapper.style.opacity = '0';
                                        setTimeout(() => colWrapper.remove(), 400);
                                    }
                                    
                                    updateCount(data.new_total);
                                    return; // Exit here so the default logic below doesn't fire
                                }
                            }
                            // --- END NEW LOGIC ---

                            // Default removal logic for all other page types (Announcements, Courses, etc.)
                            let targetElement = cardToRemove;

                            // --- NEW LOGIC: Prevent empty grid gaps for Links ---
                            // If it's a link, target the outer column wrapper instead of just the inner card
                            if (itemToDeleteType === 'link') {
                                const colWrapper = cardToRemove.closest('.col-12');
                                if (colWrapper) {
                                    targetElement = colWrapper;
                                }
                            }

                            targetElement.style.transition = 'opacity 0.4s ease';
                            targetElement.style.opacity = '0';
                            updateCount(data.new_total);

                            if (itemToDeleteType === 'course') { updateUnits(data.new_units); }

                            setTimeout(() => {
                                targetElement.remove();
                            }, 400);
                        }
                    } else {
                        alert(`Error deleting ${itemToDeleteType}: ` + data.error);
                    }
                })
                .catch(error => console.error('Error:', error));
            });
        });
    }

    function updateCount(newTotal) {
        if (newTotal !== undefined) {
            // 1. Update the big number on the actual page
            // FIX: Changed itemType to itemToDeleteType
            const pageTotal = document.getElementById(`${itemToDeleteType}-page-total-count`);
            
            if (pageTotal) {
                pageTotal.style.opacity = '0';
                setTimeout(() => {
                    pageTotal.textContent = newTotal;
                    pageTotal.style.opacity = '1';
                }, 150);
            }

            // 2. Update the little red notification badge in the sidebar (if it exists)
            const badge = document.getElementById(`${itemToDeleteType}-badge`);
            
            if (badge) {
                if (newTotal > 0) {
                    badge.textContent = newTotal;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
        }
    }

    function updateUnits(newUnits) {
        const pageUnits = document.getElementById('course-page-total-units')

        if (pageUnits) {
            pageUnits.style.opacity = '0';
            setTimeout(() => {
                pageUnits.textContent = newUnits;
                pageUnits.style.opacity = '1';
            }, 150);
        }
    }

    /* --- LIGHTBOX MODAL SCRIPT --- */
    const lightboxModal = document.getElementById('imageLightboxModal');
    
    if (lightboxModal) {
        lightboxModal.addEventListener('show.bs.modal', function (event) {
            const triggerImage = event.relatedTarget;
            const imageUrl = triggerImage.getAttribute('data-img-url');
            const modalImageDisplay = document.getElementById('lightboxImage');
            modalImageDisplay.src = imageUrl;
        });
    }


    /* =========================================
    11. LIVE SEARCH FUNCTIONALITY
    ========================================= */
    const searchInputs = document.querySelectorAll('.live-search-input');
    let debounceTimer;

    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const query = this.value.trim();
            // Identify which dropdown to use based on the input ID
            const containerId = this.id === 'desktop-search-input' ? 'desktop-search-results' : 'mobile-search-results';
            const resultsContainer = document.getElementById(containerId);
            
            clearTimeout(debounceTimer);
            
            // if (query.length < 2) {
            //     resultsContainer.style.display = 'none';
            //     return;
            // }
            
            debounceTimer = setTimeout(() => {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        resultsContainer.innerHTML = '';
                        
                        if (data.results.length === 0) {
                            resultsContainer.innerHTML = '<div class="search-result-item">No results found.</div>';
                        } else {
                            data.results.forEach(item => {
                                resultsContainer.innerHTML += `
                                    <a href="${item.url}" class="search-result-item">
                                        <div class="d-flex align-items-center gap-2">
                                            <i class="fa-solid ${item.icon}"></i>
                                            <div>
                                                <div class="fw-bold" style="font-size: 0.9rem; color: var(--text-dark)">${item.title}</div>
                                                <div class="" style="font-size: 0.75rem; color: var(--text-muted)">${item.type}</div>
                                            </div>
                                        </div>
                                    </a>
                                `;
                            });
                        }
                        resultsContainer.style.display = 'block';
                    })
                    .catch(err => console.error('Search error:', err));
            }, 300);
        });

        // Close dropdown when clicking elsewhere
        document.addEventListener('click', (e) => {
            // We now check if the click was outside the input AND outside the dropdown box
            const containerId = input.id === 'desktop-search-input' ? 'desktop-search-results' : 'mobile-search-results';
            const resultsContainer = document.getElementById(containerId);

            if (!input.contains(e.target) && !resultsContainer.contains(e.target)) {
                resultsContainer.style.display = 'none';
            }
        });

        /* =========================================
        CUSTOM HASH SCROLLING & HIGHLIGHTING
        ========================================= */

        /* =========================================
        DEBUGGING SEARCH HIGHLIGHT
        ========================================= */

        function triggerHighlight(targetId) {
            // Debug: Print the ID we are looking for
            console.log("Looking for element with selector:", targetId);
            
            const targetEl = document.querySelector(targetId);
            
            // Debug: Tell us if we found it or not
            if (targetEl) {
                console.log("SUCCESS: Found element:", targetEl);
                targetEl.classList.remove('highlight-glow');
                void targetEl.offsetWidth; 
                targetEl.classList.add('highlight-glow');

                setTimeout(() => targetEl.classList.remove('highlight-glow'), 5000);
            } else {
                console.error("ERROR: Could not find element with ID:", targetId);
                // Hint: This usually means the ID in your HTML doesn't match the ID in the URL
            }
        }

        document.addEventListener('click', function(e) {
            const link = e.target.closest('.search-result-item');
            
            if (link) {
                console.log("Search result clicked:", link.href);
                const url = new URL(link.href);
                
                const currentPath = window.location.pathname.replace(/\/$/, '');
                const targetPath = url.pathname.replace(/\/$/, '');
                
                if (currentPath === targetPath && url.hash) {
                    e.preventDefault(); 
                    
                    console.log("Attempting to scroll to hash:", url.hash);
                    
                    const targetEl = document.querySelector(url.hash);
                    
                    if (targetEl) {
                        document.querySelectorAll('.search-dropdown').forEach(el => el.style.display = 'none');
                        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        triggerHighlight(url.hash);
                    } else {
                        console.error("Could not find element for hash:", url.hash);
                    }
                }
            }
        });

        // A more robust loader that waits for full page rendering
        window.addEventListener('load', () => {
            // Check if there is a hash in the URL
            if (window.location.hash) {
                const targetId = window.location.hash;
                
                // Safety: Try up to 3 times to find the element, in case of slow animations
                let attempts = 0;
                const interval = setInterval(() => {
                    const targetEl = document.querySelector(targetId);
                    attempts++;
                    
                    if (targetEl || attempts > 5) {
                        clearInterval(interval);
                        if (targetEl) {
                            console.log("Found element on load:", targetEl);
                            targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            triggerHighlight(targetId);
                        } else {
                            console.error("Could not find element after 5 attempts:", targetId);
                        }
                    }
                }, 200); // Check every 200ms
            }
        });
    });


    /* =========================================
    WEB PUSH NOTIFICATION SETUP
    ========================================= */

    // You need to pass your PUBLIC key from your .env file into this variable later, 
    // but for now, just paste the raw string here to test the connection.
    const PUBLIC_KEY = "BNLX8AdbicZRzomXxCBRQjXd6VVoH90y6m0bxE_8FTFTJWCezMk1p2SONiCc3XPwu7Sk4jeBOHkCZM5zQGuhUR4"; 

    // A mandatory helper function that converts your public key into the security format the browser demands
    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    window.subscribeToNotifications = async function() {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            try {
                const permission = await Notification.requestPermission();
                
                if (permission === 'granted') {
                    console.log("Permission granted! Registering Service Worker...");
                    
                    const registration = await navigator.serviceWorker.register('/sw.js');
                    
                    const subscription = await registration.pushManager.subscribe({
                        userVisibleOnly: true,
                        applicationServerKey: urlBase64ToUint8Array(PUBLIC_KEY)
                    });
                    
                    console.log("SUCCESS! Sending this to the server:", subscription);
                    
                    // NEW CODE: Send the subscription to your Flask backend
                    const response = await fetch('/api/save-subscription', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(subscription)
                    });
                    
                    const result = await response.json();
                    console.log("Server response:", result);
                    
                } else {
                    console.warn("User blocked notifications.");
                }
            } catch (error) {
                console.error("Failed to subscribe:", error);
            }
        } else {
            console.warn("Push notifications are not supported.");
        }
    };

    const completeBtn = document.querySelectorAll('.complete-btn');

    completeBtn.forEach(btn => {
        // 1. Pass 'event' into the function so we can stop the default link behavior
        btn.addEventListener('click', function(event) {
            // Prevent the page from jumping to the top!
            event.preventDefault(); 
            
            const feedbackId = this.getAttribute('data-id');
            
            const taskContainer = this.closest('.feedback-item');
            const taskTitle = taskContainer.querySelector('.feedback-title');
            const statusText = taskContainer.querySelector('.feedback-status');

            taskContainer.style.transition = 'all 0.4s ease';

            fetch(`/complete-feedback/${feedbackId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                // You are explicitly passing true here
                body: JSON.stringify({ completed: true }) 
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    // Since we know it's a one-way "Mark Complete" button, 
                    // we don't need the if/else check anymore. Just update the UI!
                    
                    if (taskTitle) taskTitle.style.textDecoration = 'line-through';
                    if (statusText) statusText.textContent = 'Resolved';
                    if (taskContainer) taskContainer.style.filter = 'grayscale(1)';
                    
                    // Optional UI Polish: Hide the button so they can't click it again
                    this.style.display = 'none'; 
                }
            })
            .catch(error => console.error('Error updating task:', error));
        });
    });

    const tagForm = document.getElementById('createTagForm');
    
    if (tagForm) {
        tagForm.addEventListener('submit', function(event) {
            // Stop the browser from reloading the page
            event.preventDefault();
            
            // Gather all the inputs from the form automatically
            const formData = new FormData(tagForm);
            
            fetch('/api/create-tag', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 1. Hide the Bootstrap modal
                    const modalElement = document.getElementById('createTagModal');
                    const modalInstance = bootstrap.Modal.getInstance(modalElement);
                    modalInstance.hide();
                    
                    // 2. Clear the inputs so it's empty next time they open it
                    tagForm.reset();
                    
                    /// 3. Find the container using the new ID we added above
                    const checkboxesContainer = document.getElementById('tags-container');

                    // 4. Create the HTML matching the exact Jinja pill structure!
                    const newCheckboxHTML = `
                        <input class="btn-check" id="tags-${data.tag.id}" name="tags" type="checkbox" value="${data.tag.id}" checked>
                        <label class="btn btn-outline-primary rounded-pill btn-sm px-3" for="tags-${data.tag.id}">
                            ${data.tag.name}
                        </label>
                    `;

                    // 5. Inject the new checkbox into the page!
                    checkboxesContainer.insertAdjacentHTML('beforeend', newCheckboxHTML);
                    
                } else {
                    // Alert the user if the tag already exists or is invalid
                    alert('Error: ' + (data.error || 'Please fill out all fields.'));
                }
            })
            .catch(error => {
                console.error('Error generating tag:', error);
            });
        });
    }

    /* =========================================
       ACCOUNT SETTINGS TAB LOGIC
       ========================================= */

    // Push Notification Toggle
    const pushToggle = document.getElementById('settingsPushNotifications');

    if (pushToggle) {
        // 1. Check current status on load
        if (Notification.permission === 'granted') {
            pushToggle.checked = true;
        } else {
            pushToggle.checked = false;
        }

        // 2. Trigger on change
        pushToggle.addEventListener('change', function(e) {
            if (this.checked) {
                // Attempt to subscribe
                if (typeof window.subscribeToNotifications === 'function') {
                    window.subscribeToNotifications().then(() => {
                        // Re-check permission after the function runs
                        if (Notification.permission !== 'granted') {
                            this.checked = false; // Snap back if permission was denied/blocked
                        }
                    });
                }
            } else {
                // Browsers don't allow programmatic revocation of push permissions
                alert("To disable notifications, please click the lock icon next to your URL bar, select 'Site settings', and reset permissions.");
                this.checked = true; // Snap back to true as we can't force-disable it via JS
            }
        });
    }

    /* =========================================
       ACCOUNT SETTINGS: LIVE VALIDATION & SUBMIT
       ========================================= */

    const profileEmailInput = document.getElementById('newEmailInput');
    const currentPasswordInput = document.getElementById('currentPassword');
    const newPasswordInput = document.getElementById('newPassword');

    // LIVE TYPING: Email
    if (profileEmailInput) {
        profileEmailInput.addEventListener('input', function() {
            const isValid = window.globalConfig.emailRegex.test(this.value);
            window.setValidation(this, isValid, 'Format: 25-00000@g.batstate-u.edu.ph');
        });
    }

    // LIVE TYPING: New Password
    if (newPasswordInput) {
        newPasswordInput.addEventListener('input', function() {
            const isValid = window.globalConfig.passRegex.test(this.value);
            window.setValidation(this, isValid, 'Min 8 chars, 1 uppercase, 1 lowercase, 1 number.');
        });
    }

    // LIVE TYPING: Current Password (Clears error if they retry)
    if (currentPasswordInput) {
        currentPasswordInput.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                window.setValidation(this, true, '');
                this.classList.remove('is-valid'); 
            }
        });
    }

    // SUBMIT: Update Email
    const updateEmailForm = document.getElementById('updateEmailForm');
    if (updateEmailForm) {
        updateEmailForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Block submission if live typing regex failed
            if (profileEmailInput.classList.contains('is-invalid')) return;

            const msgBox = document.getElementById('emailMessage');
            msgBox.style.display = 'none'; // Reset message box

            fetch('/api/settings/update-email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: profileEmailInput.value })
            })
            .then(res => res.json())
            .then(data => {
                // Show SERVER message at the bottom of the form
                msgBox.style.display = 'block';
                msgBox.textContent = data.message;
                msgBox.className = data.success ? 'small mt-2 text-success fw-bold' : 'small mt-2 text-danger fw-bold';
                
                if (data.success) {
                    setTimeout(() => msgBox.style.display = 'none', 3000);
                }
            });
        });
    }

    // SUBMIT: Update Password
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Block submission if live typing regex failed
            if (newPasswordInput.classList.contains('is-invalid')) return;

            const msgBox = document.getElementById('passwordMessage');
            msgBox.style.display = 'none'; // Reset message box

            fetch('/api/settings/update-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    current_password: currentPasswordInput.value, 
                    new_password: newPasswordInput.value 
                })
            })
            .then(res => res.json())
            .then(data => {
                // Show SERVER message next to the save button
                msgBox.style.display = 'inline';
                msgBox.textContent = data.message;
                msgBox.className = data.success ? 'small me-3 text-success fw-bold' : 'small me-3 text-danger fw-bold';
                
                if (data.success) {
                    changePasswordForm.reset(); 
                    currentPasswordInput.classList.remove('is-valid', 'is-invalid');
                    newPasswordInput.classList.remove('is-valid', 'is-invalid');
                    setTimeout(() => msgBox.style.display = 'none', 4000);
                }
            });
        });
    }

    // 5. Delete Account Logic
    const deleteAccountBtn = document.getElementById('deleteAccountBtn');
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', function() {
            if (confirm("Are you absolutely sure you want to delete your account? All data will be lost.")) {
                fetch('/api/settings/delete-account', {
                    method: 'DELETE'
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = data.redirect; // Send them to login page
                    }
                });
            }
        });
    }

    const replyModal = document.getElementById('replyModal');
    const submitBtn = document.getElementById('submitReplyBtn');
    
    if (replyModal) {
        // 1. When the modal opens, grab the ID from the button that was clicked
        replyModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget; // The button that triggered the modal
            const feedbackId = button.getAttribute('data-id');
            
            // Put the ID into the hidden input field inside the modal
            document.getElementById('feedbackIdInput').value = feedbackId;
            
            // Clear out any old text from previous replies
            document.getElementById('adminReplyText').value = '';
        });

        // 2. When the admin clicks "Resolve Feedback" inside the modal
        submitBtn.addEventListener('click', function() {
            const feedbackId = document.getElementById('feedbackIdInput').value;
            const replyText = document.getElementById('adminReplyText').value;
            
            // Change button text to show it's loading
            submitBtn.textContent = 'Saving...';
            submitBtn.disabled = true;

            // Send it to the server
            fetch(`/api/reply-feedback/${feedbackId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reply_text: replyText })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Easiest way to show the new status is a clean page reload
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                submitBtn.textContent = 'Resolve Feedback';
                submitBtn.disabled = false;
            });
        });
    }

    document.querySelectorAll('.btn-pin').forEach(btn => {
        btn.addEventListener('click', function() {
            const announcementId = this.getAttribute('data-id');
            const icon = this.querySelector('i');
            
            // Disable button while processing
            this.disabled = true;

            fetch(`/api/toggle-pin/${announcementId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                this.disabled = false;
                
                if (data.success) {
                    // If you want the list to instantly re-sort, the cleanest 
                    // UX is to just reload the page smoothly!
                    window.location.reload(); 
                    
                    /* OR, if you just want to change the icon without reloading:
                    if (data.is_pinned) {
                        icon.className = 'fa-solid fa-thumbtack-slash';
                        this.setAttribute('title', 'Unpin');
                    } else {
                        icon.className = 'fa-solid fa-thumbtack';
                        this.setAttribute('title', 'Pin');
                    }
                    */
                } else {
                    alert(data.error || "Failed to pin announcement.");
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.disabled = false;
            });
        });
    });

});