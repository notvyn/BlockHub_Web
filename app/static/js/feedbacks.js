export function toggleFeedbackReplyModal() {
    const replyModal = document.getElementById('replyModal');
    const submitBtn = document.getElementById('submitReplyBtn');
    
    if (replyModal) {
        // When the modal opens, grab the ID from the button that was clicked
        replyModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget; // The button that triggered the modal
            const feedbackId = button.getAttribute('data-id');
            
            // Put the ID into the hidden input field inside the modal
            document.getElementById('feedbackIdInput').value = feedbackId;
            
            // Clear out any old text from previous replies
            document.getElementById('adminReplyText').value = '';
        });

        // When the admin clicks "Resolve Feedback" inside the modal
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
}

export function resolveFeedback() {
    const completeBtn = document.querySelectorAll('.complete-btn');

    completeBtn.forEach(btn => {
        // Pass 'event' into the function so we can stop the default link behavior
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
                    
                    // Hide the button so they can't click it again
                    this.style.display = 'none'; 
                }
            })
            .catch(error => console.error('Error updating task:', error));
        });
    });
}

export function initFeedbackForm() {
    // Safety Check: Only run if we are actually on the Add Announcement page
    const textArea = document.getElementById('feedback-message');
    if (!textArea) return; 

    const easyMDE = new EasyMDE({
        element: textArea,
        theme: "modern",
        minHeight: "100px",
        maxHeight: "200px",
        spellChecker: false,
        // Turn on the image upload feature
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
        // Define the custom upload function
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
                    // If successful, tell EasyMDE the URL to insert
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

    // Read the "Jinja Bridge" to check for Python server errors
    const hasError = textArea.getAttribute('data-has-error') === 'true';
    if (hasError && easyMDE.element.nextSibling) {
        easyMDE.element.nextSibling.classList.add('border', 'border-danger', 'rounded');
    }

    if (typeof window.initEntryValidation === 'function' ) {
        window.initEntryValidation('feedbackForm', [
            { type: 'text', id: 'title', errorId: 'error-title', message: 'Feedback Title is required.' },
            { type: 'radio', name: 'category', containerId: 'categoryContainer', errorId: 'error-category', message: 'Please select a category.' },
            { type: 'easymde', instance: easyMDE, errorId: 'error-message', message: 'Feedback content cannot be empty' }
        ]);
    }
}