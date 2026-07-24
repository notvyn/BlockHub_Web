export function cleanInputLinkModal() {
    /* =========================================
       MODAL CLEANUP ROUTINE
       ========================================= */
    const addLinkModal = document.getElementById('addLinkModal');
    
    // Create a reusable function to scrub everything clean
    function scrubLinkForm() {
        const form = document.getElementById('addLinkForm');
        if (form) form.reset(); // 1. Clear the text
        
        // 2. Hide the error messages
        const tError = document.getElementById('title-error');
        const uError = document.getElementById('url-error');
        if (tError) tError.style.display = 'none';
        if (uError) uError.style.display = 'none';
        
        // 3. Strip away all the green/red validation glows
        const inputs = form.querySelectorAll('.form-control');
        inputs.forEach(input => {
            input.classList.remove('is-valid', 'is-invalid');
        });
    }

    // Tell Bootstrap to run our scrub function every time the modal closes
    if (addLinkModal) {
        addLinkModal.addEventListener('hidden.bs.modal', function () {
            scrubLinkForm();
        });
    }
}

export function toggleLinkModal() {
/* =========================================
    UNIFIED MODAL AJAX SUBMISSION (ADD & UPDATE)
    ========================================= */
    const linkModal = document.getElementById('addLinkModal');
    const linkForm = document.getElementById('addLinkForm');

    if (linkModal) {
        // 1. SHAPESHIFT THE MODAL WHEN IT OPENS
        linkModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            
            // Check if we are adding or editing (default to add if no attribute exists)
            const mode = button.getAttribute('data-mode') || 'add';
            
            const modalTitle = linkModal.querySelector('.modal-title');
            const titleInput = document.getElementById('title');
            const urlInput = document.getElementById('url');
            
            // Hide any lingering error messages
            document.getElementById('title-error').style.display = 'none';
            document.getElementById('url-error').style.display = 'none';

            if (mode === 'edit') {
                // Transform into an UPDATE modal
                modalTitle.textContent = 'Update Quick Link';
                titleInput.value = button.getAttribute('data-title');
                urlInput.value = button.getAttribute('data-url');
                
                // Tell the form it is in edit mode and give it the specific ID
                linkForm.setAttribute('data-form-mode', 'edit');
                linkForm.setAttribute('data-target-id', button.getAttribute('data-id'));
            } else {
                // Transform into an ADD modal
                modalTitle.textContent = 'Add Quick Link';
                linkForm.reset(); // Clear the text boxes
                
                // Tell the form it is in add mode
                linkForm.setAttribute('data-form-mode', 'add');
                linkForm.removeAttribute('data-target-id');
            }
        });
    }

    if (linkForm) {
        // 2. HANDLE THE FORM SUBMISSION
        linkForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Stop page reload
            
            document.getElementById('title-error').style.display = 'none';
            document.getElementById('url-error').style.display = 'none';
            
            const formData = new FormData(this);
            const mode = this.getAttribute('data-form-mode');
            
            // Dynamically set the correct Python route based on the mode
            let fetchUrl = '/api/add-link';
            if (mode === 'edit') {
                const targetId = this.getAttribute('data-target-id');
                fetchUrl = `/api/update-link/${targetId}`;
            }
            
            fetch(fetchUrl, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // The easiest way to show the new/updated data is a clean reload
                    window.location.reload();
                } else {
                    // Show errors
                    if (data.errors.title) {
                        const err = document.getElementById('title-error');
                        err.textContent = data.errors.title[0];
                        err.style.display = 'block';
                    }
                    if (data.errors.url) {
                        const err = document.getElementById('url-error');
                        err.textContent = data.errors.url[0];
                        err.style.display = 'block';
                    }
                }
            })
            .catch(error => console.error('Fetch error:', error));
        });
    }
}

export function validateLinkForm() {
    /* =========================================
       9. LIVE FORM VALIDATION (QUICK LINKS)
       ========================================= */
    const titleInput = document.getElementById('title');
    const urlInput = document.getElementById('url');
    const titleError = document.getElementById('title-error');
    const urlError = document.getElementById('url-error');

    function isValidURL(string) {
        const urlPattern = /^(https?:\/\/)/i;
        return urlPattern.test(string);
    }

    // TITLE FIELD LOGIC
    if (titleInput && titleError) {
        titleInput.addEventListener('input', function() {
            if (this.value.trim() === '') {
                // Invalid State
                titleError.textContent = 'Please provide a title for the link.';
                titleError.style.display = 'block';
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            } else {
                // Success State!
                titleError.style.display = 'none';
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    }

    // URL FIELD LOGIC
    if (urlInput && urlError) {
        urlInput.addEventListener('input', function() {
            if (this.value.trim() === '') {
                // Invalid State (Empty)
                urlError.textContent = 'Please provide a URL.';
                urlError.style.display = 'block';
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            } else if (!isValidURL(this.value)) {
                // Invalid State (Bad Format)
                urlError.textContent = 'URL must start with http:// or https://';
                urlError.style.display = 'block';
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            } else {
                // Success State!
                urlError.style.display = 'none';
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    }
}