export function toggleDarkMode() {
    /* =========================================
       UNIFIED DARK MODE CONTROLLER
       ========================================= */
    const themeToggleBtns = document.querySelectorAll('.theme-toggle-btn');
    const settingsDarkModeToggle = document.getElementById('settingsDarkMode');

    // 1. The Master Function that changes everything at once
    function applyTheme(isDark) {
        // Change the actual CSS theme and save it
        if (isDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('blockhub_theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('blockhub_theme', 'light');
        }

        // Sync the Header Icons (Sun/Moon)
        themeToggleBtns.forEach(btn => {
            btn.innerHTML = isDark ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
        });

        // Sync the Settings Toggle Switch (if they are on the profile page)
        if (settingsDarkModeToggle) {
            settingsDarkModeToggle.checked = isDark;
        }
    }

    // 2. Initialize on Page Load (Read the saved memory)
    const savedTheme = localStorage.getItem('blockhub_theme');
    const isCurrentlyDark = (savedTheme === 'dark');
    applyTheme(isCurrentlyDark);

    // 3. Click Event for the Header Button (Sun/Moon Icon)
    themeToggleBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            // Check current state and send the OPPOSITE to the master function
            const currentlyDark = document.documentElement.getAttribute('data-theme') === 'dark';
            applyTheme(!currentlyDark); 
        });
    });

    // 4. Click Event for the Settings Tab Switch
    if (settingsDarkModeToggle) {
        settingsDarkModeToggle.addEventListener('change', function() {
            // Send the exact state of the switch (true/false) to the master function
            applyTheme(this.checked); 
        });
    }
}

export function toggleMobileSearchBar() {
    // Handle Mobile Search Expansion
    const mSearchTrigger = document.getElementById('m-search-trigger');
    const mSearchClose = document.getElementById('m-search-close');
    const mSearchOverlay = document.getElementById('m-search-overlay');
    const mSearchInput = mSearchOverlay.querySelector('input');

    if (mSearchTrigger) {
        mSearchTrigger.addEventListener('click', () => {
            mSearchOverlay.classList.add('active');
            setTimeout(() => mSearchInput.focus(), 300); // Auto-focuses the keyboard
        });
    }

    if (mSearchClose) {
        mSearchClose.addEventListener('click', () => {
            mSearchOverlay.classList.remove('active');
            mSearchInput.value = ''; // Clears the text when closed
        });
    }
}

export function toggleSidebarExpand() {
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
}

export function toggleDeleteEntry() {
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
            // Include multiple classes so it works across ALL the different pages
            cardToRemove = this.closest('.schedule-item, .card-wrapper, .feed-card, .md-task, .split-zone-row');
        });
    });

    // 2. When the "Yes, Delete" button inside ANY global modal is clicked...
    const confirmDeleteBtns = document.querySelectorAll('.confirmDeleteBtn');
    
    if (confirmDeleteBtns.length > 0) {
        confirmDeleteBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // Safety check: Don't do anything if we don't have an ID and a Type
                if (!itemToDeleteId || !itemToDeleteType) return;

                // Find the exact modal this specific button belongs to
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

                        // --- Trigger Redirect ---
                        if (redirectUrl) {
                            window.location.href = redirectUrl;
                            return; // Stop the script so it doesn't try to animate the old card
                        }

                        // Smoothly fade out the specific card we clicked
                        if (cardToRemove) {
                            
                            // --- Class Summary Date Group Cleanup ---
                            if (itemToDeleteType === 'class-summary') {
                                // Find the parent group and the bootstrap column wrapper
                                const parentGroup = cardToRemove.closest('.summary-group');
                                const colWrapper = cardToRemove.closest('.col-12') || cardToRemove;
                                
                                if (parentGroup) {
                                    // Count how many cards are currently inside this specific date block
                                    const cardsInGroup = parentGroup.querySelectorAll('.card-wrapper').length;
                                    
                                    if (cardsInGroup <= 1) {
                                        // If it's 1, this is the very last card. Fade out the entire date group.
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
                            
                            // Default removal logic for all other page types (Announcements, Courses, etc.)
                            let targetElement = cardToRemove;

                            // --- Prevent empty grid gaps for Links ---
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
}

export function toggleLiveSearch() {
    /* =========================================
    LIVE SEARCH FUNCTIONALITY
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

            // Input length limiter
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
            // check if the click was outside the input AND outside the dropdown box
            const containerId = input.id === 'desktop-search-input' ? 'desktop-search-results' : 'mobile-search-results';
            const resultsContainer = document.getElementById(containerId);

            if (!input.contains(e.target) && !resultsContainer.contains(e.target)) {
                resultsContainer.style.display = 'none';
            }
        });
    });
}

export function toggleSearchHighlight() {
    /* =========================================
    CUSTOM HASH SCROLLING & HIGHLIGHTING
    ========================================= */

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

    // waits for full page rendering
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

    /* =========================================
        DEBUGGING SEARCH HIGHLIGHT
        ========================================= */

    function triggerHighlight(targetId) {
        // Debug: Print the ID we are looking for
        // console.log("Looking for element with selector:", targetId);
        
        const targetEl = document.querySelector(targetId);
        
        // Debug: Tell us if we found it or not
        if (targetEl) {
            // console.log("SUCCESS: Found element:", targetEl);
            targetEl.classList.remove('highlight-glow');
            void targetEl.offsetWidth; 
            targetEl.classList.add('highlight-glow');

            setTimeout(() => targetEl.classList.remove('highlight-glow'), 5000);
        } else {
            console.error("ERROR: Could not find element with ID:", targetId);
            // Hint: This usually means the ID in your HTML doesn't match the ID in the URL
        }
    }
}