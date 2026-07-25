export const APP_CONFIG = {
    // Regex Rules
    emailRegex: /^\d{2}-\d{5}@g\.batstate-u\.edu\.ph$/,
    passRegex: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
    
    // Upgraded UI Helper
    setValidation: function(inputElement, isValid, errorMessage) {
        // 1. Check the immediate parent first (for standard inputs)
        let feedback = inputElement.parentElement.querySelector('.invalid-feedback');
        
        // 2. If it's trapped in an input-group, check one level higher!
        if (!feedback) {
            feedback = inputElement.parentElement.parentElement.querySelector('.invalid-feedback');
        }
        
        if (isValid) {
            inputElement.classList.remove('is-invalid');
            inputElement.classList.add('is-valid');
            if (feedback) feedback.style.display = 'none';
        } else {
            inputElement.classList.remove('is-valid');
            inputElement.classList.add('is-invalid');
            if (feedback) {
                feedback.textContent = errorMessage;
                feedback.style.display = 'block';
            }
        }
    }
};