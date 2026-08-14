export function initOnboardingTour() {
    function startOnBoarding() {
        const dashboardContainer = document.getElementById('dashboard-container');

        // Exit if the container isn't on this page
        if (!dashboardContainer) return;

        // Retrieve the dataset value
        const isLoggedIn = dashboardContainer.dataset.loggedIn === 'true';
        const isOnboarded = dashboardContainer.dataset.onboarded === 'true';

        const tourModalElement = document.getElementById('welcomeTourModal');
        if (!tourModalElement) return;

        // Only show the tour if they have NOT seen it yet
        if (isLoggedIn && !isOnboarded) {
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
                    const activeItem = carouselElement.querySelector('.carousel-item.active');
                    const items = Array.from(carouselElement.querySelectorAll('.carousel-item'));
                    const currentIndex = items.indexOf(activeItem);

                    if (currentIndex < items.length - 1) {
                        bsCarousel.next();
                    } else {
                        // Last slide: Close modal and update database
                        tourModal.hide();
                        markOnboardingComplete();
                    }
                });
            }

            // Listen for when the carousel finishes sliding
            carouselElement.addEventListener('slid.bs.carousel', function(event) {
                // Adjust index based on your total number of slides (e.g., index 4 if there are 5 slides)
                const isLastSlide = event.to === (carouselElement.querySelectorAll('.carousel-item').length - 1);
                if (isLastSlide) {
                    nextBtn.innerHTML = 'Get Started <i class="fa-solid fa-check ms-1"></i>';
                    nextBtn.classList.replace('btn-submit', 'btn-success');
                } else {
                    nextBtn.innerHTML = 'Next <i class="fa-solid fa-arrow-right ms-1"></i>';
                    nextBtn.classList.replace('btn-success', 'btn-submit');
                }
            });

            // Ensure "Skip Tour" or dismiss clicks save to the database
            dismissBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    markOnboardingComplete();
                });
            });
        }
    }

    // Function to tell the database the onboarding is complete
    function markOnboardingComplete() {
        fetch('/api/complete-onboarding', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("Onboarding permanently completed in database!");
                // Update the dataset on the element to prevent re-triggering
                const dashboardContainer = document.getElementById('dashboard-container');
                if (dashboardContainer) {
                    dashboardContainer.dataset.onboarded = 'true';
                }
            }
        });
    }

    // Optional manual finish button trigger
    const finishBtn = document.getElementById('finish-onboarding-btn');
    if (finishBtn) {
        finishBtn.addEventListener('click', markOnboardingComplete);
    }

    // Run the check on initialization
    startOnBoarding();
}