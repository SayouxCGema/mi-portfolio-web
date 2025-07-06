// Contenido para: static/js/script.js

// Nos aseguramos de que el script se ejecute solo cuando todo el HTML ha sido cargado.
document.addEventListener("DOMContentLoaded", function() {

    // --- LÓGICA PARA LA ANIMACIÓN DE FADE-IN AL HACER SCROLL ---
    
    // 1. Seleccionamos todos los elementos que tienen la clase 'fade-in'.
    const fadeElements = document.querySelectorAll('.fade-in');

    // 2. Configuramos el "observador". Esto es una herramienta moderna del navegador
    //    que es muy eficiente para detectar si algo está en la pantalla.
    const observerOptions = {
        root: null, // Observa en relación con la ventana del navegador.
        threshold: 0.1, // Se activa cuando el 10% del elemento es visible.
    };

    // 3. Creamos el observador con una función que se ejecutará cada vez que un elemento observado cambie su visibilidad.
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            // `entry.isIntersecting` es `true` si el elemento está visible.
            if (entry.isIntersecting) {
                // 4. Si es visible, añadimos la clase 'visible' al elemento.
                //    Esta clase está definida en nuestro CSS para cambiar la opacidad y la posición.
                entry.target.classList.add('visible');
                
                // 5. Una vez animado, dejamos de observarlo para no gastar recursos.
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // 6. Finalmente, le decimos al observador que empiece a "vigilar" cada uno de los elementos que seleccionamos.
    fadeElements.forEach(el => {
        observer.observe(el);
    });

});