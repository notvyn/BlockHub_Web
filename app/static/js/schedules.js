export function initScheduleForm() {
    if (typeof window.initEntryValidation === 'function') {
        window.initEntryValidation('courseScheduleForm', [
            { type: 'radio', name: 'day', containerId: 'scheduleContainer', errorId: 'error-day', message: 'Please select a day.'},
            { type: 'date', id: 'start_time', errorId: 'error-start_time', message: 'Please select a start time.'},
            { type: 'date', id: 'end_time', errorId: 'error-end_time', message: 'Please select an end time.'},
            { type: 'text', id: 'room', errorId: 'error-room', message: 'Please enter a room.'}
        ]);
    }
}