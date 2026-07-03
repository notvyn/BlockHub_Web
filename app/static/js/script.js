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