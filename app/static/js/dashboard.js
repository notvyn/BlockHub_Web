export function initOnboardingTour() {
    const tourModalElement = document.getElementById('welcomeTourModal');
    if (!tourModalElement) return;

    const hasSeenTour = localStorage.getItem('blockhub_onboarding_complete');

    if (!hasSeenTour) {
        const tourModal = new bootstrap.Modal(tourModalElement);
        tourModal.show();

        // Set up the Carousel logic
        const carouselElement = document.getElementById('onboardingCarousel');
        const bsCarousel = new bootstrap.Carousel(carouselElement, {
            interval: false, // Prevent auto-sliding
            wrap: false      // Stop at the last slide
        });

        const nextBtn = document.getElementById('tourNextBtn');
        const dismissBtns = document.querySelectorAll('.tour-dismiss-btn');

        // Handle the "Next" Button clicks
        if (nextBtn) {
            nextBtn.addEventListener('click', function() {
                // Check if we are on the final slide (Slide index 3)
                const activeItem = carouselElement.querySelector('.carousel-item.active');
                const items = Array.from(carouselElement.querySelectorAll('.carousel-item'));
                const currentIndex = items.indexOf(activeItem);

                if (currentIndex < items.length - 1) {
                    // Slide to the next one
                    bsCarousel.next();
                } else {
                    // We are on the last slide, so close the modal
                    tourModal.hide();
                    localStorage.setItem('blockhub_onboarding_complete', 'true');
                }
            });
        }

        // Listen for when the carousel finishes sliding
        carouselElement.addEventListener('slid.bs.carousel', function(event) {
            // If it's the last slide, change the button text
            const isLastSlide = event.to === 4;
            if (isLastSlide) {
                nextBtn.innerHTML = 'Get Started <i class="fa-solid fa-check ms-1"></i>';
                nextBtn.classList.replace('btn-submit', 'btn-success'); // Optional visual pop
            } else {
                nextBtn.innerHTML = 'Next <i class="fa-solid fa-arrow-right ms-1"></i>';
                nextBtn.classList.replace('btn-success', 'btn-submit');
            }
        });

        // Ensure "Skip Tour" clicks save to memory so it doesn't pop up again
        dismissBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                localStorage.setItem('blockhub_onboarding_complete', 'true');
            });
        });
    }
}