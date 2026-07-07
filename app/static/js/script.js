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
});
