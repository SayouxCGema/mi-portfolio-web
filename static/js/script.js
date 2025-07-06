// Contenido para: static/js/script.js

document.addEventListener("DOMContentLoaded", function() {

    // --- LÓGICA PARA LA ANIMACIÓN DE FADE-IN AL HACER SCROLL ---
    const fadeElements = document.querySelectorAll('.fade-in');
    
    if (fadeElements.length > 0) {
        const observerOptions = {
            root: null,
            threshold: 0.1,
        };

        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        fadeElements.forEach(el => observer.observe(el));
    }

    // Ya no necesitamos el código de Swiper.js, lo hemos eliminado.
});