document.addEventListener('DOMContentLoaded', function() {
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

    const checkboxes = document.querySelectorAll('.task-checkbox');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const deadlineId = this.getAttribute('data-id');
            const isCompleted = this.checked;
            
            // Find the text container next to this specific checkbox
            const textContainer = document.getElementById(`task-text-${deadlineId}`);

            // Send the background whisper to Flask
            fetch(`/complete-deadline/${deadlineId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ completed: isCompleted })
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    // If Flask says it saved to the DB successfully, update the visuals!
                    if (isCompleted) {
                        textContainer.classList.add('task-done-text');
                    } else {
                        // Removes the strikethrough if you uncheck it
                        textContainer.classList.remove('task-done-text'); 
                    }
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });

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
});
