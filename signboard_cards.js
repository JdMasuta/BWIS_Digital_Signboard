class CardSlideshow {
    constructor(container) {
        this.container = container;
        this.slides = container.querySelectorAll('.card-slide');
        this.prevBtn = container.querySelector('.prev-btn');
        this.nextBtn = container.querySelector('.next-btn');
        this.currentIndex = 0;
        this.slideInterval = null;
        
        this.init();
    }

    init() {
        // Add event listeners
        this.prevBtn.addEventListener('click', () => this.prevSlide());
        this.nextBtn.addEventListener('click', () => this.nextSlide());
        
        // Start automatic slideshow
        this.startSlideshow();
        
        // Pause on hover
        this.container.addEventListener('mouseenter', () => this.pauseSlideshow());
        this.container.addEventListener('mouseleave', () => this.startSlideshow());
    }

    showSlide(index) {
        // Remove active class from all slides
        this.slides.forEach(slide => slide.classList.remove('active'));
        
        // Handle wrap-around
        if (index >= this.slides.length) {
            this.currentIndex = 0;
        } else if (index < 0) {
            this.currentIndex = this.slides.length - 1;
        } else {
            this.currentIndex = index;
        }
        
        // Show current slide
        this.slides[this.currentIndex].classList.add('active');
    }

    nextSlide() {
        this.showSlide(this.currentIndex + 1);
    }

    prevSlide() {
        this.showSlide(this.currentIndex - 1);
    }

    startSlideshow() {
        if (this.slideInterval) return;
        this.slideInterval = setInterval(() => this.nextSlide(), 5000);
    }

    pauseSlideshow() {
        if (this.slideInterval) {
            clearInterval(this.slideInterval);
            this.slideInterval = null;
        }
    }
}

// Initialize slideshows when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const cardModules = document.querySelectorAll('.card-module');
    cardModules.forEach(module => new CardSlideshow(module));
});
