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
    // Grab all our new filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    // Grab all the task containers
    const deadlines = document.querySelectorAll('.deadline-item');

    if (filterButtons) {
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
        });
    }
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