export function completeDeadline() {
    const checkboxes = document.querySelectorAll('.task-checkbox');
    // const badge = document.getElementById('deadline-badge');

    // Check if current page is on the Archive page
    const isArchivePage = !!document.getElementById('deadline-archive-page-total-count');

    if (checkboxes) {
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
                            
                            // Dim the card if it's done, bring it to full brightness if missed
                            taskContainer.style.opacity = isCompleted ? '0.75' : '1';
                        }

                        updateBadges(data.new_total, data.archive_total);
                    }
                })
                .catch(error => console.error('Error updating task:', error));
            });
        });
    }
}

export function filterDeadline() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const deadlines = document.querySelectorAll('.deadline-item');
    const emptyMsgDiv = document.querySelector('#deadline-empty-msg'); // Grab the single master div

    if (filterButtons.length === 0) return;

    filterButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault(); 

            const filterType = this.getAttribute('data-filter');

            // Visual Update
            filterButtons.forEach(b => b.classList.remove('fw-bold'));
            this.classList.add('fw-bold');

            let visibleCount = 0;

            // Loop through tasks and toggle visibility
            deadlines.forEach(item => {
                const days = parseInt(item.getAttribute('data-days'));
                
                // Cleaner boolean logic
                let shouldShow = (filterType === 'all') || 
                                 (filterType === 'urgent' && days <= 2) || 
                                 (filterType === 'week' && days <= 7);

                item.style.display = shouldShow ? 'flex' : 'none'; 
                
                if (shouldShow) visibleCount++;
            });
            
            // Update the single Fallback Message
            if (emptyMsgDiv) {
                if (visibleCount === 0) {
                    // Inject the specific text based on the filter
                    if (filterType === 'all') emptyMsgDiv.textContent = 'No upcoming deadlines. Enjoy the free time!';
                    else if (filterType === 'urgent') emptyMsgDiv.textContent = 'No urgent deadlines pending right now.';
                    else if (filterType === 'week') emptyMsgDiv.textContent = 'No pending deadlines for the next 7 days.';
                    
                    emptyMsgDiv.style.display = 'block';
                } else {
                    // Hide it if we found tasks
                    emptyMsgDiv.style.display = 'none';
                }
            }
        });
    });
}


// Helper function to update the red numbers smoothly
// with 'archiveTotal' to update the number on the Archive page
function updateBadges(newTotal, archiveTotal) {
    const deadlinePageTotal = document.getElementById('deadline-page-total-count');
    const deadlineArchivePageTotal = document.getElementById('deadline-archive-page-total-count');
    const badge = document.getElementById('deadline-badge');

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

export function initDeadlineForm() {
    // 1. Safety Check: Only run if the deadline form is on the screen
    const form = document.getElementById('deadlineForm');
    if (!form) return;

    // 2. Initialize Flatpickr instances
    const fpDateGiven = flatpickr("#date_given", {
        altInput: true,
        altFormat: "D - M d, Y", 
        dateFormat: "Y-m-d",     
        allowInput: true
    });

    const fpDueDate = flatpickr("#due_date", {
        altInput: true,
        altFormat: "D - M d, Y", 
        dateFormat: "Y-m-d",     
        allowInput: true
    });

    if (typeof window.initEntryValidation === 'function') {
        window.initEntryValidation('deadlineForm', [
            { type: 'text', id: 'description', errorId: 'error-description', message: 'A title is required.' },
            { type: 'radio', name: 'course', containerId: 'courseContainer', errorId: 'error-course', message: 'Please select a course.' },
            { type: 'radio', name: 'category', containerId: 'categoryContainer', errorId: 'error-category', message: 'Please select a category.' },
            { type: 'radio', name: 'status', containerId: 'statusContainer', errorId: 'error-status', message: 'Please select a status.' },
            { type: 'flatpickr', instance: fpDateGiven, errorId: 'error-date_given', message: 'Please select a start date.' },
            { type: 'flatpickr', instance: fpDueDate, errorId: 'error-due_date', message: 'Please select a due date.' }
        ]);
    }
}