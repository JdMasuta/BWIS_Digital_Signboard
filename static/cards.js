document.addEventListener('DOMContentLoaded', function() {
    const cardModules = document.querySelectorAll('.card-module');
    
    cardModules.forEach(module => {
        const slides = module.querySelectorAll('.card-slide');
        const prevBtn = module.querySelector('.prev-btn');
        const nextBtn = module.querySelector('.next-btn');
        let currentSlide = 0;

        // Only setup if we have slides
        if (slides.length === 0) return;

        function showSlide(index) {
            // Hide all slides
            slides.forEach(slide => slide.classList.remove('active'));
            
            // Calculate new index with wrapping
            currentSlide = (index + slides.length) % slides.length;
            
            // Show new slide
            slides[currentSlide].classList.add('active');
        }

        // Setup click handlers
        prevBtn.addEventListener('click', () => showSlide(currentSlide - 1));
        nextBtn.addEventListener('click', () => showSlide(currentSlide + 1));

        // Auto advance slides every 5 seconds
        setInterval(() => showSlide(currentSlide + 1), 5000);
        
        // Show first slide
        showSlide(0);
    });
});
