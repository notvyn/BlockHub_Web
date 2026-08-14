export function initCourseForm() {
    if (typeof window.initEntryValidation === 'function') {
        window.initEntryValidation('courseForm', [
            { type: 'text', id: 'title', errorId: 'error-title', message: 'Course title is required.'},
            { type: 'text', id: 'code', errorId: 'error-code', message: 'Course code is required.'},
            { type: 'float', id: 'units', errorId: 'error-units', message: 'Please enter a valid course units.'},
            { type: 'text', id: 'instructor', errorId: 'error-instructor', message: 'Course instructor is required.'},
            { type: 'email', id: 'instructor_email', optional:true, errorId: 'error-instructor_email', message: 'Email should end by g.batstate-u.edu.ph'}
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

            // 1. Visual Feedback: Lock the button and show a spinner
            const originalContent = bulkUploadBtn.innerHTML;
            bulkUploadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Importing...';
            bulkUploadBtn.disabled = true;

            // 2. Package the PDF file
            const formData = new FormData();
            formData.append('schedule_pdf', file);

            // 3. Send it to your Python Bulk Import API
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
            
            // 4. Clear the file input so the same file can be uploaded again if needed
            this.value = '';
        });
    }
}