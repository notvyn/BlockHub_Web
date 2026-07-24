export function toggleFeedbackReplyModal() {
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
}