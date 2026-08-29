export function initCourseForm() {
    if (typeof window.initEntryValidation === 'function') {
        window.initEntryValidation('courseForm', [
            { type: 'text', id: 'title', errorId: 'error-title', message: 'Course title is required.'},
            { type: 'text', id: 'code', errorId: 'error-code', message: 'Course code is required.'},
            { type: 'float', id: 'units', errorId: 'error-units', message: 'Please enter a valid course units.'},
            { type: 'text', id: 'instructor', errorId: 'error-instructor', message: 'Course instructor is required.'},
            { type: 'email', id: 'instructor_email', optional: true, errorId: 'error-instructor_email', message: 'Email should end by g.batstate-u.edu.ph'}
        ]);
    }
}

export function initCoursePage() {
    const bulkUploadInput = document.getElementById('bulk-schedule-upload');
    const bulkUploadBtn = document.getElementById('bulk-upload-btn');

    if (bulkUploadInput && bulkUploadBtn) {
        bulkUploadInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (!file) return;

            // Visual Feedback: Lock the button and show a spinner
            const originalContent = bulkUploadBtn.innerHTML;
            bulkUploadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Importing...';
            bulkUploadBtn.disabled = true;

            // Package the PDF file
            const formData = new FormData();
            formData.append('schedule_pdf', file);

            // Send it to your Python Bulk Import API
            fetch('/api/bulk-import-schedule', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message || "Schedules imported successfully!");
                    // Refresh the page to instantly display the new Master Schedule and Course Cards
                    window.location.reload(); 
                } else {
                    alert("Error: " + data.error);
                    // Reset the button if it fails
                    bulkUploadBtn.innerHTML = originalContent;
                    bulkUploadBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                alert("Something went wrong communicating with the server.");
                // Reset the button if the network fails
                bulkUploadBtn.innerHTML = originalContent;
                bulkUploadBtn.disabled = false;
            });
            
            // Clear the file input so the same file can be uploaded again if needed
            this.value = '';
        });
    }
}

export function initTermConfig() {
    const saveBtn = document.getElementById('save-term-btn');
    
    if (saveBtn) {
        saveBtn.addEventListener('click', function(event) {
            event.preventDefault(); 
            
            const dateInput = document.getElementById('modal-semester-start');
            const newDate = dateInput.value;
            
            // Validate input
            if (!newDate) {
                dateInput.classList.add('is-invalid');
                return;
            }
            dateInput.classList.remove('is-invalid');

            // Visual Loading State
            const originalHTML = this.innerHTML;
            this.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Saving...';
            this.disabled = true;

            // 3. Send to Backend
            fetch('/api/update-semester-start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start_date: newDate })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Success State
                    this.innerHTML = '<i class="fa-solid fa-check me-2"></i>Saved!';
                    this.style.backgroundColor = '#198754'; 
                    this.style.borderColor = '#198754';
                    
                    // Smooth reload to apply the new dates across the whole app
                    setTimeout(() => window.location.reload(), 600);
                } else {
                    // Error State
                    alert("Failed to update: " + data.error);
                    this.innerHTML = originalHTML;
                    this.disabled = false;
                }
            })
            .catch(err => {
                console.error("Network Error:", err);
                alert("A network error occurred.");
                this.innerHTML = originalHTML;
                this.disabled = false;
            });
        });
    }
}

export function toggleCourseSyllabusModal() {
    // --- PDF UPLOAD LOGIC ---
    // (Remains unchanged, as it correctly handles dynamic IDs)
    document.querySelectorAll('input[type="file"][id^="syllabus-upload-"]').forEach(fileInput => {
        fileInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (!file) return; 

            const courseId = this.id.split('-').pop();
            const uploadBtn = this.nextElementSibling;
            const originalBtnHtml = uploadBtn.innerHTML;
            
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Extracting...';

            const formData = new FormData();
            formData.append('file', file);

            fetch(`/api/upload-syllabus/${courseId}`, {
                method: 'POST',
                body: formData 
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Syllabus extraction successful!');
                    window.location.reload();
                } else {
                    if (data.fallback) {
                        // alert('Could not auto-extract the tables. The PDF was saved for manual viewing.');
                        alert('Could not extract the tables. This feature is still under development, not accurate enough to use for every CIS.');
                        window.location.reload(); 
                    } else {
                        alert('Error: ' + data.error);
                        uploadBtn.disabled = false;
                        uploadBtn.innerHTML = originalBtnHtml;
                        this.value = ''; 
                    }
                }
            })
            .catch(error => {
                console.error('Upload Error:', error);
                alert('A network error occurred while uploading.');
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = originalBtnHtml;
                this.value = ''; 
            });
        });
    });

    // --- MANUAL SYLLABUS ENTRY LOGIC ---
    // Using Event Delegation to handle multiple modals effortlessly
    document.addEventListener('click', function(event) {
        
        // Add Assessment Row Button
        if (event.target.closest('.add-assessment-btn')) {
            const addBtn = event.target.closest('.add-assessment-btn');
            const currentModal = addBtn.closest('.modal'); 
            const container = currentModal.querySelector('.assessment-list-container');
            
            if (container) {
                const newRow = document.createElement('div');
                newRow.className = 'd-flex flex-column flex-md-row gap-2 mb-3 assessment-row';
                // Using Bootstrap input-group to lock the % symbol to the right
                newRow.innerHTML = `
                    <input type="text" class="form-control form-control-sm bg-transparent assessment-name" placeholder="Task Name (e.g., Prelim Exam)">
                    <select class="form-select form-select-sm bg-transparent assessment-category" style="width: auto; min-width: 130px;">
                        <option value="quiz">Quiz</option>
                        <option value="exam">Major Exam</option>
                        <option value="project">Project</option>
                        <option value="laboratory">Laboratory</option>
                        <option value="activity">Activity/Exercise</option>
                        <option value="presentation">Presentation</option>
                    </select>
                    <div class="input-group input-group-sm" style="width: 110px;">
                        <input type="text" class="form-control bg-transparent assessment-weight" placeholder="Weight">
                        <span class="input-group-text bg-transparent text-muted border-start-0">%</span>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-row-btn"><i class="fa-solid fa-xmark"></i></button>
                `;
                container.appendChild(newRow);
            }
            return;
        }

        // Remove Row Button
        if (event.target.closest('.remove-row-btn')) {
            event.target.closest('.assessment-row').remove();
            return;
        }

        // Save Week Button (Updates Individual Syllabus AND Master Calendar)
        if (event.target.closest('.save-manual-week-btn')) {
            const saveBtn = event.target.closest('.save-manual-week-btn');
            const currentModal = saveBtn.closest('.modal');
            const courseId = currentModal.id.split('-').pop();

            const selectedWeeks = Array.from(currentModal.querySelectorAll('input[name="target_weeks"]:checked')).map(cb => cb.value);
            if (selectedWeeks.length === 0) {
                saveBtn.innerHTML = '<span class="text-warning">Select a week!</span>';
                setTimeout(() => saveBtn.innerHTML = 'Save Week', 2000);
                return;
            }

            const topicsInput = currentModal.querySelector('.manual-topics');
            const topics = topicsInput ? topicsInput.value : '';

            const assessments = [];
            currentModal.querySelectorAll('.assessment-row').forEach(row => {
                const name = row.querySelector('.assessment-name').value;
                const category = row.querySelector('.assessment-category').value;
                let weight = row.querySelector('.assessment-weight').value.trim();

                // Automatically append % if missing
                if (weight !== '' && !weight.endsWith('%')) {
                    weight += '%';
                }

                if (name.trim() !== '') {
                    assessments.push({ name: name, category: category, weight: weight });
                }
            });

            const originalBtnHtml = saveBtn.innerHTML;
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Saving...';

            fetch(`/api/manual-syllabus/${courseId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ weeks: selectedWeeks, topics: topics, assessments: assessments })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    saveBtn.innerHTML = '<i class="fa-solid fa-check me-2"></i>Saved!';
                    
                    // Fetch the page in the background to get the fresh HTML for both modals
                    fetch(window.location.href)
                    .then(res => res.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');

                        // 1. Update the Individual Syllabus Timeline
                        const newTimeline = doc.querySelector(`#syllabus-data-view-${courseId}`);
                        if (newTimeline) {
                            document.querySelector(`#syllabus-data-view-${courseId}`).innerHTML = newTimeline.innerHTML;
                        }

                        // 2. Update the Master Calendar Timeline
                        const newMasterTimeline = doc.querySelector('#masterCalendarModal .timeline-container');
                        const currentMasterTimeline = document.querySelector('#masterCalendarModal .timeline-container');
                        if (newMasterTimeline && currentMasterTimeline) {
                            currentMasterTimeline.innerHTML = newMasterTimeline.innerHTML;
                            // Re-trigger the active toggle to preserve the user's view
                            const activeToggle = document.querySelector('input[name="calendarToggle"]:checked');
                            if (activeToggle) activeToggle.dispatchEvent(new Event('change'));
                        }

                        // After a brief pause, smoothly swap the views back
                        setTimeout(() => {
                            currentModal.querySelectorAll('input[name="target_weeks"]').forEach(cb => cb.checked = false);
                            if (topicsInput) topicsInput.value = '';
                            currentModal.querySelector('.assessment-list-container').innerHTML = ''; 
                            
                            saveBtn.disabled = false;
                            saveBtn.innerHTML = originalBtnHtml;

                            currentModal.querySelector(`#syllabus-manual-form-${courseId}`).classList.add('d-none');
                            currentModal.querySelector(`#syllabus-data-view-${courseId}`).classList.remove('d-none');
                        }, 200);
                    });

                } else {
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = '<span class="text-danger">Failed to save</span>';
                    setTimeout(() => saveBtn.innerHTML = originalBtnHtml, 2000);
                }
            })
            .catch(error => {
                console.error('Network Error:', error);
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<span class="text-danger">Network Error</span>';
                setTimeout(() => saveBtn.innerHTML = originalBtnHtml, 2000);
            });
        }

        // Edit Week Button
        if (event.target.closest('.edit-week-btn')) {
            event.stopPropagation();
            const editBtn = event.target.closest('.edit-week-btn');
            const currentModal = editBtn.closest('.modal');
            const courseId = currentModal.id.split('-').pop();
            const weekNum = editBtn.getAttribute('data-week');

            fetch(`/api/syllabus-week/${courseId}/${weekNum}`)
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    // Hide timeline view, show manual form accurately
                    currentModal.querySelector(`#syllabus-data-view-${courseId}`).classList.add('d-none');
                    const form = currentModal.querySelector(`#syllabus-manual-form-${courseId}`);
                    form.classList.remove('d-none');

                    // Check the correct week pill and uncheck others
                    form.querySelectorAll('input[name="target_weeks"]').forEach(cb => cb.checked = false);
                    const targetCb = form.querySelector(`#manual-w${weekNum}-${courseId}`);
                    if (targetCb) targetCb.checked = true;

                    // Populate topics
                    form.querySelector('.manual-topics').value = data.topics || '';

                    // Populate assessments
                    const container = form.querySelector('.assessment-list-container');
                    container.innerHTML = ''; // Clear default row
                    
                    data.assessments.forEach(task => {
                        const row = document.createElement('div');
                        row.className = 'd-flex flex-column flex-md-row gap-2 mb-3 assessment-row';
                        
                        // Strip the % sign from the DB string so it doesn't double up in the UI
                        const cleanWeight = task.weight ? task.weight.replace('%', '').trim() : '';

                        row.innerHTML = `
                            <input type="text" class="form-control form-control-sm bg-transparent assessment-name" value="${task.name}">
                            <select class="form-select form-select-sm bg-transparent assessment-category" style="width: auto; min-width: 130px;">
                                <option value="quiz" ${task.category === 'quiz' ? 'selected' : ''}>Quiz</option>
                                <option value="exam" ${task.category === 'exam' ? 'selected' : ''}>Major Exam</option>
                                <option value="project" ${task.category === 'project' ? 'selected' : ''}>Project</option>
                                <option value="laboratory" ${task.category === 'laboratory' ? 'selected' : ''}>Laboratory</option>
                                <option value="activity" ${task.category === 'activity' ? 'selected' : ''}>Activity/Exercise</option>
                                <option value="presentation" ${task.category === 'presentation' ? 'selected' : ''}>Presentation</option>
                            </select>
                            <div class="input-group input-group-sm" style="width: 110px;">
                                <input type="text" class="form-control bg-transparent assessment-weight" value="${cleanWeight}" placeholder="Weight">
                                <span class="input-group-text bg-transparent text-muted border-start-0">%</span>
                            </div>
                            <button type="button" class="btn btn-sm btn-outline-danger remove-row-btn"><i class="fa-solid fa-xmark"></i></button>
                        `;
                        container.appendChild(row);
                    });
                } else {
                    alert('Could not fetch week data.');
                }
            });
            return;
        }

        // Delete Week Button (Instant UI Update, NO Reload)
        if (event.target.closest('.delete-week-btn')) {
            event.stopPropagation();
            const delBtn = event.target.closest('.delete-week-btn');

            // Soft Confirm State
            if (!delBtn.dataset.confirm) {
                delBtn.dataset.confirm = "true";
                const originalHtml = delBtn.innerHTML;
                delBtn.innerHTML = '<span class="badge bg-danger">Sure?</span>';
                
                setTimeout(() => {
                    if (delBtn) {
                        delBtn.dataset.confirm = "";
                        delBtn.innerHTML = originalHtml;
                    }
                }, 3000);
                return;
            }

            // Actual Delete Execution
            const currentModal = delBtn.closest('.modal');
            const courseId = currentModal.id.split('-').pop();
            const weekNum = delBtn.getAttribute('data-week');
            const weekBlock = delBtn.closest('.week-block'); // Find the specific week container

            delBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

            fetch(`/api/syllabus-week/${courseId}/${weekNum}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    // INSTANTLY rip the week block out of the HTML. No reload!
                    weekBlock.remove(); 
                } else {
                    alert('Failed to delete week.');
                    delBtn.innerHTML = '<i class="fa-solid fa-trash" style="font-size: 0.85rem;"></i>';
                }
            });
            return;
        }

        // Granular Task Delete (Instant UI Update, NO Reload)
        if (event.target.closest('.delete-task-btn')) {
            event.stopPropagation();
            const delBtn = event.target.closest('.delete-task-btn');

            // Soft Confirm State
            if (!delBtn.dataset.confirm) {
                delBtn.dataset.confirm = "true";
                const originalHtml = delBtn.innerHTML;
                delBtn.innerHTML = '<span class="badge bg-danger">Sure?</span>';
                
                setTimeout(() => {
                    if (delBtn) {
                        delBtn.dataset.confirm = "";
                        delBtn.innerHTML = originalHtml;
                    }
                }, 3000);
                return;
            }
            
            // Actual Delete Execution
            const taskId = delBtn.getAttribute('data-task-id');
            const taskRow = delBtn.closest('.d-flex'); // Find the specific row
            
            delBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

            fetch(`/api/syllabus-task/${taskId}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    // INSTANTLY rip the task out of the HTML. No reload!
                    taskRow.remove(); 
                }
            });
            return;
        }
    });
}

export function toggleMasterCalendar() {
    const toggleCombined = document.getElementById('toggleCombined');
    const toggleTopics = document.getElementById('toggleTopics');
    const toggleAssessments = document.getElementById('toggleAssessments');
    const emptyState = document.getElementById('mc-empty-state');
    
    function updateCalendarView() {
        if (!toggleTopics || !toggleAssessments || !toggleCombined) return;
        
        const isCombined = toggleCombined.checked;
        const isTopics = toggleTopics.checked;
        const isAssessments = toggleAssessments.checked;
        
        let visibleBlocks = 0;
        
        // Topic Items: Safely toggle Bootstrap visibility classes
        document.querySelectorAll('.mc-topic-item').forEach(el => {
            if (isCombined || isTopics) {
                el.classList.remove('d-none');
                el.classList.add('d-flex');
            } else {
                el.classList.remove('d-flex');
                el.classList.add('d-none');
            }
        });
        
        // Assessment Items: Safely toggle Bootstrap visibility classes
        document.querySelectorAll('.mc-assessment-item').forEach(el => {
            if (isCombined || isAssessments) {
                el.classList.remove('d-none');
                el.classList.add('d-flex');
            } else {
                el.classList.remove('d-flex');
                el.classList.add('d-none');
            }
        });

        // Hide empty week containers
        document.querySelectorAll('#masterCalendarModal .week-block').forEach(weekBlock => {
            const items = Array.from(weekBlock.querySelectorAll('.mc-topic-item, .mc-assessment-item'));
            // Check if at least one item does NOT have the 'd-none' hidden class
            const hasVisibleItems = items.some(el => !el.classList.contains('d-none'));
            
            if (hasVisibleItems) {
                weekBlock.classList.remove('d-none');
                visibleBlocks++;
            } else {
                weekBlock.classList.add('d-none');
            }
        });

        // 4. Show empty state if zero items match
        if (emptyState) {
            const totalBlocks = document.querySelectorAll('#masterCalendarModal .week-block').length;
            if (visibleBlocks === 0 && totalBlocks > 0) {
                emptyState.classList.remove('d-none');
            } else {
                emptyState.classList.add('d-none');
            }
        }
    }

    if (toggleTopics && toggleAssessments && toggleCombined) {
        toggleCombined.addEventListener('change', updateCalendarView);
        toggleTopics.addEventListener('change', updateCalendarView);
        toggleAssessments.addEventListener('change', updateCalendarView);
        updateCalendarView(); // Run initial state check on load
    }
}