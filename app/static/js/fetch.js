document.addEventListener('DOMContentLoaded', function() {
    let itemToDeleteId = null;
    let itemToDeleteType = null;
    let cardToRemove = null;

    // 1. When ANY trash can button is clicked...
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            // Grab the ID and the new 'data-type' attribute
            itemToDeleteId = this.getAttribute('data-id');
            itemToDeleteType = this.getAttribute('data-type'); 
            
            // This targets the specific container. 
            // We include multiple classes here so it works across ALL your different pages!
            cardToRemove = this.closest('.card-wrapper, .feed-card, .md-task, .split-zone-row'); 
        });
    });

    // 2. When the "Yes, Delete" button inside the global modal is clicked...
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            // Safety check: Don't do anything if we don't have an ID and a Type
            if (!itemToDeleteId || !itemToDeleteType) return;

            // Dynamically inject the type and ID into the fetch URL
            fetch(`/delete-entry/${itemToDeleteType}/${itemToDeleteId}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Hide the Bootstrap modal
                    const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
                    deleteModal.hide();

                    // Smoothly fade out the specific card we clicked
                    if (cardToRemove) {
                        cardToRemove.style.transition = 'opacity 0.4s ease';
                        cardToRemove.style.opacity = '0';
                        setTimeout(() => {
                            cardToRemove.remove();
                        }, 400);
                    }
                } else {
                    alert(`Error deleting ${itemToDeleteType}: ` + data.error);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }

    /* --- LIGHTBOX MODAL SCRIPT --- */
    const lightboxModal = document.getElementById('imageLightboxModal');
    
    if (lightboxModal) {
        lightboxModal.addEventListener('show.bs.modal', function (event) {
            const triggerImage = event.relatedTarget;
            const imageUrl = triggerImage.getAttribute('data-img-url');
            const modalImageDisplay = document.getElementById('lightboxImage');
            modalImageDisplay.src = imageUrl;
        });
    }
});