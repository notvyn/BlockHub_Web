export const APP_CONFIG = {
    // Regex Rules
    emailRegex: /^\d{2}-\d{5}@g\.batstate-u\.edu\.ph$/, // BatStateU domain email
    passRegex: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/, // Should include atleast 8 characters with lowercase and uppercase letter, and a number
    
    // Upgraded UI Helper
    setValidation: function(inputElement, isValid, errorMessage) {
        // Check the immediate parent first (for standard inputs)
        let feedback = inputElement.parentElement.querySelector('.invalid-feedback');
        
        // If it's trapped in an input-group, check one level higher!
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