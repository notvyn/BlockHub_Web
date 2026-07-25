// js/tools.js

export function initWallpaperGenerator() {
    // 1. SAFETY CHECK: Only run if the wallpaper export div exists on the page
    const wallpaper = document.getElementById('wallpaper-export');
    if (!wallpaper) return;

    // Grab core elements
    const bgLayer = document.getElementById('wallpaper-bg-layer');
    const blockInput = document.getElementById('block-input');
    const wallpaperTitle = document.querySelector('.wallpaper-title-2'); 
    const wallpaperHeader = document.querySelector('.wallpaper-header');
    const glassCard = wallpaper.querySelector('.schedule-glass-card');

    // ==========================================
    // 2. LIVE TYPING (Title Input)
    // ==========================================
    if (wallpaperTitle && blockInput) {
        blockInput.addEventListener('input', function() {
            if (blockInput.value.trim() !== "") {
                wallpaperTitle.textContent = blockInput.value;
            } else {
                wallpaperTitle.textContent = 'Block/Section';
            }
        });
    }

    // ==========================================
    // 3. TEMPLATE SWITCHING
    // ==========================================
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

    // ==========================================
    // 4. THEME SWITCHING
    // ==========================================
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

    // ==========================================
    // 5. ADVANCED SLIDERS & CUSTOM BACKGROUND
    // ==========================================
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

    // ==========================================
    // 6. DOWNLOAD WALLPAPER (html2canvas)
    // ==========================================
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