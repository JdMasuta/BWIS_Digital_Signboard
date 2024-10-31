document.addEventListener('DOMContentLoaded', function() {
    const cardModules = document.querySelectorAll('.card-module');
    cardModules.forEach(module => {
        const slides = module.querySelectorAll('.card-slide');
        const prevBtn = module.querySelector('.prev-btn');
        const nextBtn = module.querySelector('.next-btn');
        let currentSlide = 0;

        function showSlide(index) {
            slides.forEach(slide => slide.classList.remove('active'));
            currentSlide = (index + slides.length) % slides.length;
            slides[currentSlide].classList.add('active');
        }

        prevBtn?.addEventListener('click', () => showSlide(currentSlide - 1));
        nextBtn?.addEventListener('click', () => showSlide(currentSlide + 1));

        // Auto advance slides every 5 seconds
        setInterval(() => showSlide(currentSlide + 1), 5000);
    });
});
