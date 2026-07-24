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