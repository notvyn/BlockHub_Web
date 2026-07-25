// UNIVERSAL ENTRY FORM VALIDATOR (GLOBAL)
window.initEntryValidation = function(formId, fieldsConfig) {
    const form = document.getElementById(formId);
    if (!form) return;

    const validators = fieldsConfig.map(field => {
        return function() {
            let isValid = true;
            let targetElement = null;
            let applyBoxBorder = false;
            let dynamicMessage = field.message; // Default message

            // A. Logic Check
            if (field.type === 'text') {
                targetElement = document.getElementById(field.id);
                if (targetElement) isValid = targetElement.value.trim() !== '';
            } 
            else if (field.type === 'float') {
                targetElement = document.getElementById(field.id);
                if (targetElement) {
                    const val = targetElement.value.trim();
                    const numVal = parseFloat(val);
                    
                    // Must not be empty, must be a number, finite, AND greater than or equal to 0
                    isValid = val !== '' && !isNaN(numVal) && isFinite(val) && numVal >= 0;
                }
            }
            else if (field.type === 'url') {
                targetElement = document.getElementById(field.id);
                if (targetElement) {
                    const val = targetElement.value.trim();
                    
                    if (field.optional && val === '') {
                        isValid = true; // It's valid if it's optional and left blank!
                    } else if (val === '') {
                        isValid = false; // It's empty, and NOT optional
                        dynamicMessage = field.messageEmpty || field.message;
                    } else {
                        // THE MULTI-URL FIX
                        // This checks for a valid link, followed by optional commas or spaces, 
                        // and allows it to repeat infinitely until the end of the text.
                        const urlPattern = /^(?:(?:https?:\/\/[^\s,]+|\[[^\]]+\]\(https?:\/\/[^\s)]+\))[\s,]*)+$/i;
                        isValid = urlPattern.test(val);
                        dynamicMessage = field.messageFormat || field.message;
                    }
                }
            }
            else if (field.type === 'radio') {
                const radios = document.querySelectorAll(`input[name="${field.name}"]`);
                isValid = Array.from(radios).some(radio => radio.checked);
                if (field.containerId) {
                    targetElement = document.getElementById(field.containerId);
                    applyBoxBorder = true; 
                }
            } 
            else if (field.type === 'easymde') {
                isValid = field.instance.value().trim() !== '';
                if (field.instance.element.nextSibling) {
                    targetElement = field.instance.element.nextSibling;
                    applyBoxBorder = true;
                }
            }
            else if (field.type === 'flatpickr') {
                isValid = field.instance.selectedDates.length > 0;
                targetElement = field.instance.altInput || field.instance.input;
            }

            // B. Visual Updates
            const errorDiv = document.getElementById(field.errorId);
            
            if (isValid) {
                if (targetElement) {
                    targetElement.classList.remove('is-invalid', 'is-valid');
                    if (applyBoxBorder) targetElement.classList.remove('border', 'border-danger', 'p-2', 'rounded');
                }
                if (errorDiv) errorDiv.style.display = 'none';
            } else {
                if (targetElement) {
                    targetElement.classList.remove('is-valid');
                    targetElement.classList.add('is-invalid');
                    if (applyBoxBorder) targetElement.classList.add('border', 'border-danger', 'p-2', 'rounded');
                }
                if (errorDiv) {
                    // Use the dynamically selected error message
                    errorDiv.textContent = dynamicMessage;
                    errorDiv.style.display = 'block';
                }
            }
            return isValid;
        };
    });

    // 2. Attach Live Event Listeners
    fieldsConfig.forEach((field, index) => {
        const validateFn = validators[index];
        
        // Ensure 'url' is added to this listener group alongside text and float!
        if (field.type === 'text' || field.type === 'float' || field.type === 'url') {
            const input = document.getElementById(field.id);
            if (input) input.addEventListener('input', validateFn);
        } else if (field.type === 'radio') {
            const radios = document.querySelectorAll(`input[name="${field.name}"]`);
            radios.forEach(radio => radio.addEventListener('change', validateFn));
        } else if (field.type === 'easymde') {
            field.instance.codemirror.on('change', validateFn); 
        } else if (field.type === 'flatpickr') {
            field.instance.config.onChange.push(validateFn);
        }
    });

    // 3. Gatekeeper
    form.addEventListener('submit', function(e) {
        let isFormValid = true;
        validators.forEach(validateFn => {
            if (!validateFn()) isFormValid = false;
        });
        if (!isFormValid) e.preventDefault();
    });
};

export function setAnchorToAnnouncement() {
    // 1. Target every single link specifically inside the announcement content
    const contentLinks = document.querySelectorAll('.card-content a');
    
    contentLinks.forEach(link => {
        // 2. Force the link to open in a new tab
        link.setAttribute('target', '_blank');
        
        // 3. Security best practice: Prevents the new tab from maliciously hijacking your dashboard page
        link.setAttribute('rel', 'noopener noreferrer');
    });
}