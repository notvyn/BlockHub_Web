document.addEventListener('DOMContentLoaded', function() {
    let itemToDeleteId = null;
    let itemToDeleteType = null;
    let itemCount = null;
    let cardToRemove = null;
    let redirectUrl = null;

    // 1. When ANY trash can button is clicked...
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            // Grab the ID and the new 'data-type' attribute
            itemToDeleteId = this.getAttribute('data-id');
            itemToDeleteType = this.getAttribute('data-type');

            redirectUrl = this.getAttribute('data-redirect');
            
            if (itemToDeleteType !== 'course-schedule') {
                itemCount = this.getAttribute('data-count');
            }
            
            // This targets the specific container. 
            // We include multiple classes here so it works across ALL your different pages!
            cardToRemove = this.closest('.schedule-item, .card-wrapper, .feed-card, .md-task, .split-zone-row');
        });
    });

    // 2. When the "Yes, Delete" button inside ANY global modal is clicked...
    // FIX 1: Use querySelectorAll so we can use .forEach()
    const confirmDeleteBtns = document.querySelectorAll('.confirmDeleteBtn');
    
    if (confirmDeleteBtns.length > 0) {
        confirmDeleteBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // Safety check: Don't do anything if we don't have an ID and a Type
                if (!itemToDeleteId || !itemToDeleteType) return;

                // FIX 2: Find the exact modal this specific button belongs to
                const currentModalElement = this.closest('.modal');

                // Dynamically inject the type and ID into the fetch URL
                fetch(`/delete-entry/${itemToDeleteType}/${itemToDeleteId}`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        
                        // Hide whichever Bootstrap modal we are currently using
                        if (currentModalElement) {
                            const activeModal = bootstrap.Modal.getInstance(currentModalElement);
                            activeModal.hide();
                        }

                        // --- NEW LOGIC: Trigger Redirect ---
                        if (redirectUrl) {
                            window.location.href = redirectUrl;
                            return; // Stop the script here so it doesn't try to animate the old card!
                        }

                        // Smoothly fade out the specific card we clicked
                        if (cardToRemove) {
                            
                            // --- NEW LOGIC: Class Summary Date Group Cleanup ---
                            if (itemToDeleteType === 'class-summary') {
                                // Find the parent group and the bootstrap column wrapper
                                const parentGroup = cardToRemove.closest('.summary-group');
                                const colWrapper = cardToRemove.closest('.col-12') || cardToRemove;
                                
                                if (parentGroup) {
                                    // Count how many cards are currently inside this specific date block
                                    const cardsInGroup = parentGroup.querySelectorAll('.card-wrapper').length;
                                    
                                    if (cardsInGroup <= 1) {
                                        // If it's 1, this is the very last card! Fade out the entire date group.
                                        parentGroup.style.transition = 'opacity 0.4s ease';
                                        parentGroup.style.opacity = '0';
                                        setTimeout(() => parentGroup.remove(), 400);
                                    } else {
                                        // If there are other cards left, just remove this specific column
                                        colWrapper.style.transition = 'opacity 0.4s ease';
                                        colWrapper.style.opacity = '0';
                                        setTimeout(() => colWrapper.remove(), 400);
                                    }
                                    
                                    updateCount(data.new_total);
                                    return; // Exit here so the default logic below doesn't fire
                                }
                            }
                            // --- END NEW LOGIC ---

                            // Default removal logic for all other page types (Announcements, Courses, etc.)
                            cardToRemove.style.transition = 'opacity 0.4s ease';
                            cardToRemove.style.opacity = '0';
                            updateCount(data.new_total);

                            if (itemToDeleteType === 'course') { updateUnits(data.new_units); }

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
        });
    }

    function updateCount(newTotal) {
        if (newTotal !== undefined) {
            // 1. Update the big number on the actual page
            // FIX: Changed itemType to itemToDeleteType
            const pageTotal = document.getElementById(`${itemToDeleteType}-page-total-count`);
            
            if (pageTotal) {
                pageTotal.style.opacity = '0';
                setTimeout(() => {
                    pageTotal.textContent = newTotal;
                    pageTotal.style.opacity = '1';
                }, 150);
            }

            // 2. Update the little red notification badge in the sidebar (if it exists)
            const badge = document.getElementById(`${itemToDeleteType}-badge`);
            
            if (badge) {
                if (newTotal > 0) {
                    badge.textContent = newTotal;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
        }
    }

    function updateUnits(newUnits) {
        const pageUnits = document.getElementById('course-page-total-units')

        if (pageUnits) {
            pageUnits.style.opacity = '0';
            setTimeout(() => {
                pageUnits.textContent = newUnits;
                pageUnits.style.opacity = '1';
            }, 150);
        }
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