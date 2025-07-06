// Contenido para: static/js/script.js

document.addEventListener("DOMContentLoaded", function() {

    // --- LÓGICA PARA LA ANIMACIÓN DE FADE-IN AL HACER SCROLL ---
    const fadeElements = document.querySelectorAll('.fade-in');
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

    // --- INICIALIZACIÓN DEL CARRUSEL DE CLIENTES (SWIPER.JS) ---
    const swiper = new Swiper('.client-carousel', {
        // Opciones
        loop: true, // Para que el carrusel sea infinito
        autoplay: {
            delay: 2500, // Se mueve cada 2.5 segundos
            disableOnInteraction: false, // Sigue moviéndose aunque el usuario interactúe
        },
        // Cuántos logos se ven a la vez
        slidesPerView: 2,
        spaceBetween: 30,
        // Responsive breakpoints
        breakpoints: {
            // cuando la ventana es >= 640px
            640: {
              slidesPerView: 3,
              spaceBetween: 40
            },
            // cuando la ventana es >= 768px
            768: {
              slidesPerView: 4,
              spaceBetween: 50
            },
            // cuando la ventana es >= 1024px
            1024: {
              slidesPerView: 5,
              spaceBetween: 60
            }
        },
        // Botones de navegación (opcional)
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
    });

});