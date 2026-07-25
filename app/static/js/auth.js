import { APP_CONFIG } from './config.js';

export function eyeToggle() {
    const eyeToggle = document.querySelectorAll('.eye-toggle');
    if (eyeToggle) {
        eyeToggle.forEach(eye => {
            eye.addEventListener('click', function() {
                const parent = this.closest('.input-group');
                const passwordInput = parent.querySelector('.form-control');

                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    this.innerHTML = '<i class="fa-solid fa-eye"></i>';
                }
                else {
                    passwordInput.type = 'password';
                    this.innerHTML = '<i class="fa-solid fa-eye-slash"></i>';
                }
            });
        });
    }
}

export function validateSignUpInput() {
    // 1. Grab the inputs
    const nameInput = document.getElementById('name')
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirm_password');

    // --- NAME VALIDATION ---
    if (nameInput) {
        nameInput.addEventListener('input', function() {
            const isValid = this.value !== '';
            APP_CONFIG.setValidation(this, isValid, 'Please enter a valid name');
        });
    }

    // --- EMAIL VALIDATION ---
    if (emailInput) {
        emailInput.addEventListener('input', function() {
            const isValid = APP_CONFIG.emailRegex.test(this.value);
            APP_CONFIG.setValidation(this, isValid, 'Format: 25-00000@g.batstate-u.edu.ph');
        });
    }

    // --- PASSWORD VALIDATION ---
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const isValid = APP_CONFIG.passRegex.test(this.value);
            APP_CONFIG.setValidation(this, isValid, 'Min 8 chars, 1 uppercase, 1 lowercase, 1 number.');
            
            // If they fix the main password, force the confirm box to re-check itself
            if (confirmInput.value) {
                confirmInput.dispatchEvent(new Event('input'));
            }
        });
    }

    // --- CONFIRM PASSWORD VALIDATION ---
    if (confirmInput) {
        confirmInput.addEventListener('input', function() {
            // It must match exactly AND the main password must actually be strong!
            const isMatch = this.value === passwordInput.value && this.value !== '';
            const isMainValid = APP_CONFIG.passRegex.test(passwordInput.value);
            
            APP_CONFIG.setValidation(this, (isMatch && isMainValid), 'Passwords do not match or main password is weak.');
        });
    }
}