// js/tools.js

export function initWallpaperGenerator() {
    // SAFETY CHECK: Only run if the wallpaper export div exists on the page
    const wallpaper = document.getElementById('wallpaper-export');
    if (!wallpaper) return;

    // Grab core elements
    const bgLayer = document.getElementById('wallpaper-bg-layer');
    const blockInput = document.getElementById('block-input');
    const wallpaperTitle = document.querySelector('.wallpaper-title-2'); 
    const wallpaperHeader = document.querySelector('.wallpaper-header');
    const glassCard = wallpaper.querySelector('.schedule-glass-card');

    // LIVE TYPING (Title Input)
    if (wallpaperTitle && blockInput) {
        blockInput.addEventListener('input', function() {
            if (blockInput.value.trim() !== "") {
                wallpaperTitle.textContent = blockInput.value;
            } else {
                wallpaperTitle.textContent = 'Block/Section';
            }
        });
    }

    // TEMPLATE SWITCHING
    const templateBtns = document.querySelectorAll('.btn-template');
    templateBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const templateName = this.getAttribute('data-template');
            
            // Swap classes on the wallpaper
            wallpaper.classList.remove('template-sunset', 'template-vintage', 'template-modern');
            wallpaper.classList.add(templateName);

            // Update button styles dynamically
            templateBtns.forEach(b => b.classList.replace('btn-dark', 'btn-outline-dark'));
            this.classList.replace('btn-outline-dark', 'btn-dark');
        });
    });

    // THEME SWITCHING
    const themeBtns = document.querySelectorAll('.theme-btn');
    const opacitySlider = document.getElementById('opacity-slider');
    
    themeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const themeName = this.getAttribute('data-theme');
            
            wallpaper.classList.remove('theme-dark', 'theme-light');
            wallpaper.classList.add(themeName);

            const alpha = opacitySlider ? opacitySlider.value : 0;
            if (glassCard) {
                if (themeName === 'theme-light') {
                    glassCard.style.backgroundColor = `rgba(255, 255, 255, ${alpha})`;
                } else {
                    glassCard.style.backgroundColor = `rgba(0, 0, 0, ${alpha})`;
                }
            }

            themeBtns.forEach(b => b.classList.replace('btn-dark', 'btn-outline-dark'));
            this.classList.replace('btn-outline-dark', 'btn-dark');
        });
    });

    // ADVANCED SLIDERS & CUSTOM BACKGROUND
    if (opacitySlider && glassCard) {
        const opacityValDisplay = document.getElementById('opacity-val');
        opacitySlider.addEventListener('input', function() {
            const alpha = this.value;
            if (opacityValDisplay) opacityValDisplay.textContent = alpha; 

            const isLight = wallpaper.classList.contains('theme-light');
            const isVintage = wallpaper.classList.contains('template-vintage');

            glassCard.style.backgroundColor = isLight ? `rgba(255, 255, 255, ${alpha})` : `rgba(0, 0, 0, ${alpha})`;
            if (isVintage && wallpaperHeader) {
                wallpaperHeader.style.backgroundColor = isLight ? `rgba(255, 255, 255, ${alpha})` : `rgba(0, 0, 0, ${alpha})`;
            }
        });
    }

    const bgOpacitySlider = document.getElementById('bg-opacity-slider');
    if (bgOpacitySlider && bgLayer) {
        const bgOpacityValDisplay = document.getElementById('bg-opacity-val');
        bgOpacitySlider.addEventListener('input', function() {
            if (bgOpacityValDisplay) bgOpacityValDisplay.textContent = this.value; 
            bgLayer.style.opacity = this.value;
        });
    }

    const cardPositionSlider = document.getElementById('card-position-slider');
    if (cardPositionSlider && glassCard) {
        const cardPosValDisplay = document.getElementById('card-pos-val');
        cardPositionSlider.addEventListener('input', function() {
            if (cardPosValDisplay) cardPosValDisplay.textContent = this.value;
            glassCard.style.marginBottom = `${this.value}rem`;
        });
    }

    const bgZoomSlider = document.getElementById('bg-zoom-slider');
    if (bgZoomSlider && bgLayer) {
        const bgZoomValDisplay = document.getElementById('bg-zoom-val');
        bgZoomSlider.addEventListener('input', function() {
            if (bgZoomValDisplay) bgZoomValDisplay.textContent = this.value;
            bgLayer.style.backgroundSize = `${this.value}%`;
        });
    }

    const bgUpload = document.getElementById('bg-upload');
    if (bgUpload) {
        bgUpload.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const imageUrl = URL.createObjectURL(file);
                bgLayer.style.backgroundImage = `url('${imageUrl}')`;
            }
        });
    }

    // A reusable function to attach deletion logic to existing AND newly injected buttons
    function attachRemoveListeners() {
        document.querySelectorAll('.btn-remove-course').forEach(btn => {
            // Clone and replace to prevent duplicate events on old buttons
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', function() {
                const courseCode = this.getAttribute('data-course');
                const safeCourseCode = courseCode.replace(/\s+/g, '');
                
                const courseItems = document.querySelectorAll(`.course-item-${safeCourseCode}`);
                
                courseItems.forEach(item => {
                    const classId = item.getAttribute('data-id');
                    const timeEl = document.getElementById(`preview-time-${classId}`);
                    const courseEl = document.getElementById(`preview-course-${classId}`);
                    
                    if (timeEl && courseEl) {
                        const scheduleRow = timeEl.closest('.schedule-row');
                        const timeContainer = timeEl.closest('.time-text');
                        
                        timeEl.remove();
                        courseEl.remove();
                        
                        if (timeContainer && timeContainer.querySelectorAll('p').length === 0) {
                            scheduleRow.remove(); 
                        }
                    }
                });
                
                const managerBlock = document.getElementById(`manager-course-${safeCourseCode}`);
                if (managerBlock) managerBlock.remove();
            });
        });
    }

    // Fire once on initial page load for Jinja-rendered templates
    attachRemoveListeners();

    const pdfUpload = document.getElementById('pdf-upload');

    if (pdfUpload) {
        pdfUpload.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('schedule_pdf', file);

            glassCard.innerHTML = '<div class="text-center py-5"><i class="fa-solid fa-spinner fa-spin fa-2x text-white"></i><p class="mt-2 text-white">Analyzing Schedule...</p></div>';

            fetch('/api/parse-schedule', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // CLEAR BOTH CONTAINERS
                    glassCard.innerHTML = '';
                    const accordionBody = document.querySelector('#collapseSchedules .accordion-body');
                    if (accordionBody) accordionBody.innerHTML = '';

                    // REBUILD THE WALLPAPER CANVAS
                    const dayMap = {
                        'Monday': 'mon', 'Tuesday': 'tues', 'Wednesday': 'wed', 
                        'Thursday': 'thurs', 'Friday': 'fri', 'Saturday': 'sat', 'Sunday': 'sun'
                    };

                    // Define the strict chronological order
                    const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

                    // Loop through the ordered array
                    dayOrder.forEach(day => {
                        const classes = data.data[day];
                        
                        // Only build a row if there are actually classes scheduled that day
                        if (classes && classes.length > 0) {
                            let rowHtml = `
                                <div class="schedule-row">
                                    <div class="left-panel">
                                        <div class="day-text">${dayMap[day]}</div>
                                        <div class="time-text">
                            `;
                            classes.forEach(c => { rowHtml += `<p id="preview-time-${c.id}">${c.time}</p>`; });
                            rowHtml += `</div></div><div class="right-panel">`;
                            classes.forEach(c => { rowHtml += `<p class="mb-0" id="preview-course-${c.id}">${c.course} | ${c.room}</p>`; });
                            rowHtml += `</div></div>`; 
                            
                            glassCard.insertAdjacentHTML('beforeend', rowHtml);
                        }
                    });

                    // REBUILD THE ACCORDION MANAGER
                    if (accordionBody && data.course_data) {
                        for (const [courseCode, courseInfo] of Object.entries(data.course_data)) {
                            const safeCourseCode = courseCode.replace(/\s+/g, '');
                            
                            let courseHtml = `
                                <div class="course-manager-block px-4 py-1" id="manager-course-${safeCourseCode}">
                                    <div class="d-flex justify-content-between align-items-start pt-3 mb-1 border-top border-bottom border-1" style="border-color: var(--hue-shade) !important;">
                                        <p class="fs-6 fw-bold text-dark ">
                                            ${courseCode} <span class="text-muted fw-normal">| ${courseInfo.title}</span>
                                        </p>
                                        <button type="button" class="btn btn-outline-danger btn-sm px-3 py-1 fw-bold btn-remove-course" data-course="${courseCode}">
                                            <i class="fa-solid fa-close"></i>
                                        </button>
                                    </div>
                                    <div class="d-flex flex-wrap gap-2 bg-transparent">
                            `;
                            
                            courseInfo.classes.forEach(c => {
                                courseHtml += `
                                    <div class="course-item-${safeCourseCode} p-2 flex-grow-1" data-id="${c.id}" style="min-width: 150px;">
                                        <div class="d-flex flex-column">
                                            <span class="fw-bold text-dark" style="font-size: 0.8rem;">${c.day}</span>
                                            <span class="text-muted" style="font-size: 0.75rem;">${c.time} <span style="opacity: 0.5;">|</span> ${c.room}</span>
                                        </div>
                                    </div>
                                `;
                            });
                            
                            courseHtml += `</div></div>`;
                            accordionBody.insertAdjacentHTML('beforeend', courseHtml);
                        }
                    }

                    // BIND THE NEW DELETE BUTTONS
                    attachRemoveListeners();

                } else {
                    alert("Error: " + data.error);
                    glassCard.innerHTML = '<div class="text-center p-3 text-white">Failed to parse PDF. Please try manually.</div>';
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                alert("Something went wrong communicating with the server.");
            });
            
            // Reset file input to allow re-uploads
            this.value = '';
        });
    }

    // DOWNLOAD WALLPAPER (html2canvas)
    const downloadBtn = document.getElementById('download-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', async function() {
            const originalText = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating HD...';
            downloadBtn.disabled = true;

            await new Promise(r => setTimeout(r, 100));
            await document.fonts.ready;

            try {
                // html2canvas is globally available because it is loaded in the <head>
                const canvas = await html2canvas(wallpaper, {
                    scale: 2, 
                    useCORS: true, 
                    allowTaint: true,
                    backgroundColor: null,
                    onclone: function (clonedDocument) {
                        const clonedWallpaper = clonedDocument.getElementById('wallpaper-export');
                        clonedWallpaper.style.transform = 'none';
                        clonedWallpaper.style.position = 'relative'; 
                    }
                });

                canvas.toBlob(function(blob) {
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.download = 'Class_Schedule.jpg';
                    link.href = url;
                    
                    document.body.appendChild(link);
                    link.click();
                    
                    setTimeout(() => {
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                    }, 150);
                }, "image/jpeg", 0.95);

            } catch (err) {
                console.error("Error generating wallpaper:", err);
                alert("There was an issue saving the image. Try opening this link directly in Safari or Chrome!");
            } finally {
                downloadBtn.innerHTML = originalText;
                downloadBtn.disabled = false;
            }
        });
    }
}