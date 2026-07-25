export function initCourseForm() {
    if (typeof window.initEntryValidation === 'function') {
        window.initEntryValidation('courseForm', [
            { type: 'text', id: 'title', errorId: 'error-title', message: 'Course title is required.'},
            { type: 'text', id: 'code', errorId: 'error-code', message: 'Course code is required.'},
            { type: 'float', id: 'units', errorId: 'error-units', message: 'Please enter a valid course units.'},
            { type: 'text', id: 'instructor', errorId: 'error-instructor', message: 'Course instructor is required.'},
            { type: 'url', id: 'instructor_email', optional: true, errorId: 'error-instructor_email', messageFormat: 'URL must start with http:// or https://' }
        ]);
    }
}