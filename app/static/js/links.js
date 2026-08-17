export function cleanInputLinkModal() {
    /* MODAL CLEANUP ROUTINE */
    const addLinkModal = document.getElementById('addLinkModal');
    
    function scrubLinkForm() {
        const form = document.getElementById('addLinkForm');
        if (form) form.reset(); 
        
        // Hide ALL error messages, including the new category error
        const tError = document.getElementById('title-error');
        const uError = document.getElementById('url-error');
        const cError = document.getElementById('category-error');
        if (tError) tError.style.display = 'none';
        if (uError) uError.style.display = 'none';
        if (cError) cError.style.display = 'none';
        
        // Strip away validation glows from inputs AND selects
        const inputs = form.querySelectorAll('.form-control, .form-select');
        inputs.forEach(input => {
            input.classList.remove('is-valid', 'is-invalid');
        });
    }

    if (addLinkModal) {
        addLinkModal.addEventListener('hidden.bs.modal', function () {
            scrubLinkForm();
        });
    }
}

export function toggleLinkModal() {
    /* UNIFIED MODAL AJAX SUBMISSION (ADD & UPDATE) */
    const linkModal = document.getElementById('addLinkModal');
    const linkForm = document.getElementById('addLinkForm');

    if (linkModal) {
        linkModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const mode = button.getAttribute('data-mode') || 'add';
            
            const modalTitle = linkModal.querySelector('.modal-title');
            const titleInput = document.getElementById('title');
            const urlInput = document.getElementById('url');
            const categoryInput = document.getElementById('category'); // WTForms automatically assigns this ID
            
            // Hide lingering errors
            document.getElementById('title-error').style.display = 'none';
            document.getElementById('url-error').style.display = 'none';
            document.getElementById('category-error').style.display = 'none';

            if (mode === 'edit') {
                modalTitle.textContent = 'Update Quick Link';
                titleInput.value = button.getAttribute('data-title');
                urlInput.value = button.getAttribute('data-url');
                categoryInput.value = button.getAttribute('data-category'); // Set the dropdown to match the DB
                
                linkForm.setAttribute('data-form-mode', 'edit');
                linkForm.setAttribute('data-target-id', button.getAttribute('data-id'));
            } else {
                modalTitle.textContent = 'Add Quick Link';
                linkForm.reset(); 
                
                linkForm.setAttribute('data-form-mode', 'add');
                linkForm.removeAttribute('data-target-id');
            }
        });
    }

    if (linkForm) {
        linkForm.addEventListener('submit', function(e) {
            e.preventDefault(); 
            
            document.getElementById('title-error').style.display = 'none';
            document.getElementById('url-error').style.display = 'none';
            document.getElementById('category-error').style.display = 'none';
            
            const formData = new FormData(this);
            const mode = this.getAttribute('data-form-mode');
            
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
                    window.location.reload();
                } else {
                    // Show errors for all fields if validation fails
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
                    if (data.errors.category) {
                        const err = document.getElementById('category-error');
                        err.textContent = data.errors.category[0];
                        err.style.display = 'block';
                    }
                }
            })
            .catch(error => console.error('Fetch error:', error));
        });
    }
}

export function validateLinkForm() {
    /* LIVE FORM VALIDATION (QUICK LINKS) */
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
                // Success State
                urlError.style.display = 'none';
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    }
}

export function toggleLinkPin() {
    /* LINK PINNING LOGIC */
    document.querySelectorAll('.btn-link-pin').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const linkId = this.getAttribute('data-id');
            
            fetch(`/api/toggle-link-pin/${linkId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    // re-sort dynamic grid by a quick page reload
                    window.location.reload();
                }
            })
            .catch(error => console.error('Error toggling pin:', error));
        });
    });
}