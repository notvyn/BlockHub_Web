export function getCourseRadios() {
    // GET COURSE RADIOS
    // 1. Target the elements
    const courseRadios = document.querySelectorAll('.course-radio');
    const scheduleContainer = document.getElementById('dynamic-date-container');
    
    // 2. Listen for clicks on ANY course radio button
    courseRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const selectedCourseId = this.value;
            
            scheduleContainer.innerHTML = '<span class="text-muted" style="font-size: 0.85rem; font-style: italic;">Loading schedules...</span>';
            
            fetch(`/api/get-schedules/${selectedCourseId}`)
                .then(response => response.json())
                .then(data => {
                    scheduleContainer.innerHTML = '';
                    
                    if (data.schedules.length === 0) {
                        scheduleContainer.innerHTML = '<span class="text-danger fw-bold" style="font-size: 0.85rem;">No schedules found for this course.</span>';
                        return;
                    }

                    // NEW: Grab the hidden saved ID from the HTML
                    const savedScheduleId = scheduleContainer.getAttribute('data-saved-schedule');
                    
                    data.schedules.forEach(sched => {
                        // NEW: If the current loop matches the saved ID, add the 'checked' attribute
                        const isChecked = (savedScheduleId == sched.id) ? 'checked' : '';
                        
                        const htmlString = `
                            <input class="btn-check" id="schedule-${sched.id}" name="schedule" required type="radio" value="${sched.id}" ${isChecked}>
                            <label class="btn-pill" for="schedule-${sched.id}">${sched.label}</label>
                        `;
                        scheduleContainer.insertAdjacentHTML('beforeend', htmlString);
                    });
                })
                .catch(error => console.error('Error fetching schedules:', error));
        });
    });

    // NEW: Auto-trigger the loading process when the page first opens!
    // If WTForms pre-selected a course, we simulate a click on it so the schedules load instantly.
    const preSelectedCourse = document.querySelector('.course-radio:checked');
    if (preSelectedCourse) {
        preSelectedCourse.dispatchEvent(new Event('change'));
    }
    
    // 2. Listen for any clicks inside this container
    if (scheduleContainer) {
        scheduleContainer.addEventListener('change', function(e) {
            
            // 3. Ensure they actually clicked a radio button
            if (e.target && e.target.matches('input[name="schedule"]')) {
                
                // 4. Find the label attached to this radio button and read its text
                const labelText = document.querySelector(`label[for="${e.target.id}"]`).innerText;
                
                // Extract just the day part (e.g., splits "Monday | 07:00 AM" and grabs "Monday")
                const selectedDayString = labelText.split('|')[0].trim(); 
                
                // 5. Map the text string to JavaScript's numbered days (0 = Sunday, 1 = Monday)
                const daysOfWeek = {
                    'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 
                    'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6
                };
                
                const targetDayNum = daysOfWeek[selectedDayString];
                
                if (targetDayNum !== undefined) {
                    const today = new Date();
                    const currentDayNum = today.getDay();
                    
                    // 6. Calculate the math to find the most recent occurrence of that day
                    let daysToSubtract = currentDayNum - targetDayNum;
                    
                    // If the target day is ahead of us in the week (e.g., today is Tuesday(2), target is Friday(5)),
                    // we need to wrap around to the previous week's Friday.
                    if (daysToSubtract < 0) {
                        daysToSubtract += 7; 
                    }
                    
                    // 7. Calculate the exact historical date
                    const targetDate = new Date(today);
                    targetDate.setDate(today.getDate() - daysToSubtract);
                    
                    // 8. Command Flatpickr to jump to this new date instantly!
                    fpInstance.setDate(targetDate);
                }
            }
        });
    }
}

