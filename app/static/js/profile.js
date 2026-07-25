export function initUpdateProfileSettings() {
    // ==========================================
    // 1. INSTANT AVATAR PREVIEW
    // ==========================================
    const imageInput = document.getElementById('profile_pic'); 
    const imagePreview = document.getElementById('avatarPreview');

    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function(event) {
            const [file] = event.target.files;
            if (file) {
                imagePreview.src = URL.createObjectURL(file);
            }
        });
    }

    // ==========================================
    // 2. TAG SELECTION LIMITER
    // ==========================================
    const MAX_TAGS = 5;
    const tagCheckboxes = document.querySelectorAll('#tagsAccordion .user-selectable-tag'); 
    const tagCounter = document.getElementById('tagCounter');

    if (tagCheckboxes.length > 0 && tagCounter) {
        function updateTagCount() {
            let checkedCount = 0;
            tagCheckboxes.forEach(cb => { if (cb.checked) checkedCount++; });
            
            tagCounter.textContent = `${checkedCount}/${MAX_TAGS}`;
            
            if (checkedCount >= MAX_TAGS) {
                tagCounter.classList.replace('bg-secondary', 'bg-danger');
                tagCheckboxes.forEach(cb => { if (!cb.checked) cb.disabled = true; });
            } else {
                tagCounter.classList.replace('bg-danger', 'bg-secondary');
                tagCheckboxes.forEach(cb => { cb.disabled = false; });
            }
        }

        tagCheckboxes.forEach(cb => cb.addEventListener('change', updateTagCount));
        updateTagCount(); // Run once on load
    }

    // ==========================================
    // 3. INSTANT DELETE TAG (Event Delegation)
    // ==========================================
    const tagsContainer = document.getElementById('tags-container');
    if (tagsContainer) {
        tagsContainer.addEventListener('click', function(e) {
            // Check if they clicked the delete button (or the icon inside it)
            const deleteBtn = e.target.closest('.delete-btn');
            
            if (deleteBtn) {
                const tagId = deleteBtn.getAttribute('data-id');
                if (!confirm('Are you sure you want to delete this tag?')) return;

                fetch(`/tag/${tagId}/delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        deleteBtn.closest('.custom-tag-pill').remove();
                    }
                })
                .catch(err => console.error("Error deleting tag:", err));
            }
        });
    }

    // ==========================================
    // 4. CREATE / EDIT TAG MODAL LOGIC
    // ==========================================
    const tagModal = document.getElementById('createTagModal');
    const form = document.getElementById('exclusiveTagForm');
    const submitBtn = document.getElementById('exclusiveSubmitBtn');
    const alertBox = document.getElementById('modalAlertBox');

    if (tagModal && submitBtn && form) {
        // Modal Setup
        tagModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            // Safety check: if the modal is triggered by something else, skip
            if (!button) return; 

            const isAdd = button.getAttribute('data-is-add');
            const title = tagModal.querySelector('.modal-title');
            const nameInput = form.querySelector('#tag_name');
            
            alertBox.classList.add('d-none');
            form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
            form.querySelectorAll('.invalid-feedback').forEach(el => el.style.display = 'none');
            form.querySelector('#categoryContainer').classList.remove('border', 'border-danger', 'p-2', 'rounded');

            if (isAdd) {
                title.textContent = 'Create a New Tag';
                submitBtn.textContent = 'Create Tag';
                form.setAttribute('data-target-url', '/api/create-tag'); 
                nameInput.value = '';
                form.querySelectorAll('input[type="radio"]').forEach(r => r.checked = false);
            } else {
                title.textContent = 'Edit Tag';
                submitBtn.textContent = 'Save Changes';
                form.setAttribute('data-target-url', button.getAttribute('data-action'));
                nameInput.value = button.getAttribute('data-name');
                
                const category = button.getAttribute('data-category');
                const targetRadio = form.querySelector(`input[value="${category}"]`);
                if (targetRadio) targetRadio.checked = true;
            }
        });

        // Submit Handler
        submitBtn.addEventListener('click', function() {
            alertBox.classList.add('d-none');
            form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
            form.querySelectorAll('.invalid-feedback').forEach(el => el.style.display = 'none');
            const catContainer = form.querySelector('#categoryContainer');
            catContainer.classList.remove('border', 'border-danger', 'p-2', 'rounded');

            const formData = new FormData(form);
            const targetUrl = form.getAttribute('data-target-url');
            const isEdit = targetUrl.includes('/edit');

            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Saving...';
            submitBtn.disabled = true;

            fetch(targetUrl, {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;

                if (data.success) {
                    if (isEdit) {
                        window.location.reload(); 
                    } else {
                        // Notice the button here now uses data-id instead of onclick!
                        const newPill = document.createElement('div');
                        newPill.className = 'custom-tag-pill d-flex align-items-center';
                        newPill.innerHTML = `
                            <input class="btn-check" id="tags-${data.tag.id}" name="tags" type="checkbox" value="${data.tag.name}">
                            <label class="tag-label mb-0" for="tags-${data.tag.id}">${data.tag.name}</label>
                            <div class="tag-divider"></div>
                            <div class="tag-actions d-flex align-items-center">
                                <button type="button" class="tag-action-btn edit-btn px-1" title="Edit Tag"
                                        data-bs-toggle="modal" data-bs-target="#createTagModal"
                                        data-action="/tag/${data.tag.id}/edit"
                                        data-name="${data.tag.name}" data-category="${data.tag.category}">
                                    <i class="fa-solid fa-pencil" style="font-size: 0.75rem;"></i>
                                </button>
                                <button type="button" class="tag-action-btn delete-btn px-1" title="Delete Tag"
                                        data-id="${data.tag.id}">
                                    <i class="fa-solid fa-xmark" style="font-size: 0.85rem;"></i>
                                </button>
                            </div>
                        `;
                        tagsContainer.appendChild(newPill);
                        // Using Bootstrap's official instance method to hide
                        bootstrap.Modal.getInstance(tagModal).hide();
                        window.location.reload(); 
                    }
                } else {
                    if (data.error) {
                        alertBox.textContent = data.error;
                        alertBox.classList.remove('d-none');
                    }
                    if (data.errors) {
                        if (data.errors.tag_name) {
                            form.querySelector('#tag_name').classList.add('is-invalid');
                            const errName = form.querySelector('#error-tag_name');
                            errName.textContent = data.errors.tag_name[0];
                            errName.style.display = 'block';
                        }
                        if (data.errors.tag_category) {
                            catContainer.classList.add('border', 'border-danger', 'p-2', 'rounded');
                            const errCat = form.querySelector('#error-tag_category');
                            errCat.textContent = data.errors.tag_category[0];
                            errCat.style.display = 'block';
                        }
                    }
                }
            })
            .catch(err => {
                console.error("Fetch Error:", err);
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            });
        });
    }
}

export function toggleCreateTag() {
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
}

export function toggleNotificationSubscription() {
    /* =========================================
    WEB PUSH NOTIFICATION SETUP
    ========================================= */

    // 1. Find the meta tag in the HTML
    const publicKeyMeta = document.querySelector('meta[name="vapid-public-key"]');

    // 2. Extract the string from the 'content' attribute
    const PUBLIC_KEY = publicKeyMeta ? publicKeyMeta.getAttribute('content') : null;

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
}

export function toggleUserProfileUpdate() {
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
}

