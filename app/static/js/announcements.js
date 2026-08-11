

export function getReadHistory() {
    // 1. Setup: Grab authentication status from the container
    const container = document.getElementById('dashboard-container');
    
    // If the container isn't on this page, stop the function immediately
    if (!container) return; 
    
    const isLoggedIn = container.getAttribute('data-logged-in') === 'true';
    
    if (!isLoggedIn) {
        // Guest Memory Check 
        let guestReadIds = JSON.parse(localStorage.getItem('guestReadAnnouncements')) || [];
        document.querySelectorAll('.new-tag').forEach(tag => {
            let tagId = tag.id.split('-')[1]; 
            if (guestReadIds.includes(tagId)) { tag.style.display = 'none'; }
        });
    } else {
        // User is logged in. Check for guest data to sync.
        let guestReadIds = JSON.parse(localStorage.getItem('guestReadAnnouncements'));
        
        // If there is data to sync...
        if (guestReadIds && guestReadIds.length > 0) {
            
            // 1. Instantly hide the tags on the screen
            guestReadIds.forEach(id => {
                const tag = document.getElementById(`tag-${id}`);
                if (tag) tag.style.display = 'none';
            });
            
            // 2. Send the data to the Python route
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
                    // 3. Delete the local browser memory
                    localStorage.removeItem('guestReadAnnouncements');
                }
            })
            .catch(error => console.error('Error syncing data:', error));
        }
    }
}

export function initAnnouncementForm() {
    // 1. Safety Check: Only run if we are actually on the Add Announcement page
    const textArea = document.getElementById('announcement-content');
    if (!textArea) return; 

    // 2. Initialize EasyMDE with all your custom settings
    const easyMDE = new EasyMDE({
        element: textArea,
        theme: "modern",
        minHeight: "100px", 
        maxHeight: "250px",
        spellChecker: false,
        uploadImage: true,
        toolbar: [
            "bold", "italic", "strikethrough", "|", 
            "heading-1", "heading-2", "heading-3", "|", 
            "code", "quote", "|", 
            "unordered-list", "ordered-list", "|", 
            "link", "image", "horizontal-rule", "|", 
            "preview", "side-by-side", "fullscreen", "|", 
            "guide"
        ],
        imageUploadFunction: function(file, onSuccess, onError) {
            const formData = new FormData();
            formData.append('image', file);

            fetch('/upload-image', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.data && data.data.filePath) {
                    onSuccess(data.data.filePath);
                } else {
                    onError("Upload failed");
                }
            })
            .catch(err => {
                onError(err.toString());
            });
        }
    });

    // 3. Read the "Jinja Bridge" to check for Python server errors
    const hasError = textArea.getAttribute('data-has-error') === 'true';
    if (hasError && easyMDE.element.nextSibling) {
        easyMDE.element.nextSibling.classList.add('border', 'border-danger', 'rounded');
    }

    // 4. Initialize Live Frontend Validation
    if (typeof APP_CONFIG.initEntryValidation === 'function') {
        APP_CONFIG.initEntryValidation('announcementForm', [
            { type: 'text', id: 'title', errorId: 'error-title', message: 'A title is required.' },
            { type: 'easymde', instance: easyMDE, errorId: 'error-content', message: 'Announcement content cannot be empty.' },
            { type: 'url', id: 'url', optional: true, errorId: 'error-url', messageFormat: 'URL must start with http:// or https://' }
        ]);
    }
}

export function readAnnouncement() {
    // 3. The Click Event (With Navigation Pause)
    document.querySelectorAll('.announcement-link').forEach(link => {
        link.addEventListener('click', function(e) {
            // STOP the browser from navigating instantly
            e.preventDefault(); 
            
            const targetUrl = this.getAttribute('href'); 
            const announcementId = this.getAttribute('data-id');
            const tag = document.getElementById(`tag-${announcementId}`);
            
            // Visually hide the 'NEW' tag instantly
            if (tag && tag.style.display !== 'none') {
                tag.style.display = 'none';

                // Run the counter again to decrease the badge number instantly
                if (typeof updateAnnouncementBadge === 'function') {
                    updateAnnouncementBadge();
                }
            }

            const container = document.getElementById('dashboard-container');
            const isLoggedIn = container ? container.getAttribute('data-logged-in') === 'true' : true;

            if (isLoggedIn) {
                // Send the network request, and wait for it to finish
                fetch(`/mark-announcement-read/${announcementId}`, {
                    method: 'POST'
                })
                .finally(() => {
                    // NAVIGATE to the post ONLY after the server gets the message
                    window.location.href = targetUrl;
                });
            } else {
                // GUEST: Save to memory and navigate instantly
                let guestReadIds = JSON.parse(localStorage.getItem('guestReadAnnouncements')) || [];
                if (!guestReadIds.includes(announcementId)) {
                    guestReadIds.push(announcementId);
                    localStorage.setItem('guestReadAnnouncements', JSON.stringify(guestReadIds));
                }
                window.location.href = targetUrl; 
            }
        });
    });
}

export function setFileIcon() {
    /* =========================================
       SMART FILE ATTACHMENT ICONS
       ========================================= */
    document.querySelectorAll('.card-content a').forEach(link => {
        const url = link.href.toLowerCase();
        let iconClass = 'fa-link'; // Default icon
        let iconColor = 'var(--accent-purple)'; // Default color

        // Check the extension and assign the right icon and color
        if (url.endsWith('.pdf')) { 
            iconClass = 'fa-file-pdf'; 
            iconColor = '#ff5252'; 
        } else if (url.endsWith('.docx') || url.endsWith('.doc')) { 
            iconClass = 'fa-file-word'; 
            iconColor = '#42a5f5'; 
        } else if (url.endsWith('.xlsx') || url.endsWith('.csv')) { 
            iconClass = 'fa-file-excel'; 
            iconColor = '#66bb6a'; 
        } else if (url.endsWith('.pptx')) { 
            iconClass = 'fa-file-powerpoint'; 
            iconColor = '#ff7043'; 
        } else if (url.endsWith('.zip') || url.endsWith('.rar')) { 
            iconClass = 'fa-file-zipper'; 
            iconColor = '#ffca28'; 
        }

        // Create the HTML icon element
        const icon = document.createElement('i');
        icon.className = `fa-solid ${iconClass} me-2`;
        icon.style.color = iconColor;

        // Insert the icon right at the beginning of the link text
        link.prepend(icon);
    });
}

export function toggleAnnouncementPin() {
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
                    // instantly re-sort by reloading the page
                    window.location.reload(); 
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
}

export function toggleHeartReact() {
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
}

export function toggleLightboxModal() {
    const lightboxModal = document.getElementById('imageLightboxModal');
    
    if (lightboxModal) {
        lightboxModal.addEventListener('show.bs.modal', function (event) {
            // 1. Get the element that the user just clicked
            const triggerElement = event.relatedTarget;
            
            // 2. Extract the URL from the custom data attribute we added in Step 1
            const imageUrl = triggerElement.getAttribute('data-img-url');
            
            // 3. Inject the URL into the modal's <img> tag
            const modalImage = document.getElementById('lightboxImage');
            modalImage.src = imageUrl;
            
            // 4. Inject the URL into the Download button's data-url attribute
            const downloadBtn = document.getElementById('lightboxDownloadBtn');
            downloadBtn.setAttribute('data-url', imageUrl);
        });

        // Optional but recommended: Clear the image when the modal closes 
        // to prevent a brief flash of the old image the next time it opens.
        lightboxModal.addEventListener('hidden.bs.modal', function () {
            document.getElementById('lightboxImage').src = "";
        });
    }
}

/* =========================================
    DYNAMIC BADGE COUNTER
========================================= */
export function updateAnnouncementBadge() {
    // 1. Update the Dashboard Pill (Counts physical tags on the screen)
    const dashBadge = document.getElementById('announcement-badge');
    if (dashBadge) {
        let unreadCount = 0;
        document.querySelectorAll('.new-tag').forEach(tag => {
            if (tag.style.display !== 'none') unreadCount++;
        });
        dashBadge.textContent = unreadCount;
        dashBadge.style.display = unreadCount > 0 ? 'inline-block' : 'none';
    }

    // 2. Update the Global Sidebar Pill & Dot (Simply decrements the number by 1)
    const sidebarBadge = document.getElementById('sidebar-announcement-badge');
    if (sidebarBadge) {
        let currentCount = parseInt(sidebarBadge.textContent) || 0;
        let newCount = currentCount - 1;
        
        if (newCount > 0) {
            sidebarBadge.textContent = newCount;
        } else {
            // If it hits 0, hide the pill AND force the red dot to disappear
            sidebarBadge.style.display = 'none'; 
            const dot = sidebarBadge.closest('.sidebar-link').querySelector('.sidebar-badge-dot');
            if (dot) dot.style.setProperty('display', 'none', 'important');
        }
    }
}