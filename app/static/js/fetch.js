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
                            let targetElement = cardToRemove;

                            // --- NEW LOGIC: Prevent empty grid gaps for Links ---
                            // If it's a link, target the outer column wrapper instead of just the inner card
                            if (itemToDeleteType === 'link') {
                                const colWrapper = cardToRemove.closest('.col-12');
                                if (colWrapper) {
                                    targetElement = colWrapper;
                                }
                            }

                            targetElement.style.transition = 'opacity 0.4s ease';
                            targetElement.style.opacity = '0';
                            updateCount(data.new_total);

                            if (itemToDeleteType === 'course') { updateUnits(data.new_units); }

                            setTimeout(() => {
                                targetElement.remove();
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


    /* =========================================
    11. LIVE SEARCH FUNCTIONALITY
    ========================================= */
    const searchInputs = document.querySelectorAll('.live-search-input');
    let debounceTimer;

    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const query = this.value.trim();
            // Identify which dropdown to use based on the input ID
            const containerId = this.id === 'desktop-search-input' ? 'desktop-search-results' : 'mobile-search-results';
            const resultsContainer = document.getElementById(containerId);
            
            clearTimeout(debounceTimer);
            
            // if (query.length < 2) {
            //     resultsContainer.style.display = 'none';
            //     return;
            // }
            
            debounceTimer = setTimeout(() => {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        resultsContainer.innerHTML = '';
                        
                        if (data.results.length === 0) {
                            resultsContainer.innerHTML = '<div class="search-result-item">No results found.</div>';
                        } else {
                            data.results.forEach(item => {
                                resultsContainer.innerHTML += `
                                    <a href="${item.url}" class="search-result-item">
                                        <div class="d-flex align-items-center gap-2">
                                            <i class="fa-solid ${item.icon}"></i>
                                            <div>
                                                <div class="fw-bold" style="font-size: 0.9rem; color: var(--text-dark)">${item.title}</div>
                                                <div class="" style="font-size: 0.75rem; color: var(--text-muted)">${item.type}</div>
                                            </div>
                                        </div>
                                    </a>
                                `;
                            });
                        }
                        resultsContainer.style.display = 'block';
                    })
                    .catch(err => console.error('Search error:', err));
            }, 300);
        });

        // Close dropdown when clicking elsewhere
        document.addEventListener('click', (e) => {
            // We now check if the click was outside the input AND outside the dropdown box
            const containerId = input.id === 'desktop-search-input' ? 'desktop-search-results' : 'mobile-search-results';
            const resultsContainer = document.getElementById(containerId);

            if (!input.contains(e.target) && !resultsContainer.contains(e.target)) {
                resultsContainer.style.display = 'none';
            }
        });

        /* =========================================
        CUSTOM HASH SCROLLING & HIGHLIGHTING
        ========================================= */

        /* =========================================
        DEBUGGING SEARCH HIGHLIGHT
        ========================================= */

        function triggerHighlight(targetId) {
            // Debug: Print the ID we are looking for
            console.log("Looking for element with selector:", targetId);
            
            const targetEl = document.querySelector(targetId);
            
            // Debug: Tell us if we found it or not
            if (targetEl) {
                console.log("SUCCESS: Found element:", targetEl);
                targetEl.classList.remove('highlight-glow');
                void targetEl.offsetWidth; 
                targetEl.classList.add('highlight-glow');

                setTimeout(() => targetEl.classList.remove('highlight-glow'), 5000);
            } else {
                console.error("ERROR: Could not find element with ID:", targetId);
                // Hint: This usually means the ID in your HTML doesn't match the ID in the URL
            }
        }

        document.addEventListener('click', function(e) {
            const link = e.target.closest('.search-result-item');
            
            if (link) {
                console.log("Search result clicked:", link.href);
                const url = new URL(link.href);
                
                const currentPath = window.location.pathname.replace(/\/$/, '');
                const targetPath = url.pathname.replace(/\/$/, '');
                
                if (currentPath === targetPath && url.hash) {
                    e.preventDefault(); 
                    
                    console.log("Attempting to scroll to hash:", url.hash);
                    
                    const targetEl = document.querySelector(url.hash);
                    
                    if (targetEl) {
                        document.querySelectorAll('.search-dropdown').forEach(el => el.style.display = 'none');
                        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        triggerHighlight(url.hash);
                    } else {
                        console.error("Could not find element for hash:", url.hash);
                    }
                }
            }
        });

        // A more robust loader that waits for full page rendering
        window.addEventListener('load', () => {
            // Check if there is a hash in the URL
            if (window.location.hash) {
                const targetId = window.location.hash;
                
                // Safety: Try up to 3 times to find the element, in case of slow animations
                let attempts = 0;
                const interval = setInterval(() => {
                    const targetEl = document.querySelector(targetId);
                    attempts++;
                    
                    if (targetEl || attempts > 5) {
                        clearInterval(interval);
                        if (targetEl) {
                            console.log("Found element on load:", targetEl);
                            targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            triggerHighlight(targetId);
                        } else {
                            console.error("Could not find element after 5 attempts:", targetId);
                        }
                    }
                }, 200); // Check every 200ms
            }
        });
    });
});