# Contenido para: app.py
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
# Se necesita una 'secret_key' para que los mensajes flash (como "mensaje enviado con éxito") funcionen.
# Puedes cambiarla por cualquier otra cadena de texto aleatoria.
app.secret_key = 'gema-calderon-sayoux-web-secreta'

# --- DATOS PARA NO REPETIRLOS EN EL HTML ---
# Así, si tu email cambia, solo lo modificas aquí.
CONTACT_DATA = {
    "email": "gemacalderonsayoux@gmail.com",
    "linkedin": "https://www.linkedin.com/in/gema-calderon-sayoux/"
}

# Lista de packs para el menú desplegable del formulario.
SERVICE_PACKS = [
    "Web completa (WordPress o HTML)",
    "Campañas Google Ads + Analytics",
    "Estrategia de contenidos SEO",
    "Pack de horas (5h, 10h o 20h)",
    "Consulta inicial (1h)",
    "No estoy seguro/a, necesito asesoramiento"
]

# --- RUTAS DE LA APLICACIÓN ---

# Esta es la ruta principal: http://127.0.0.1:5000/
@app.route("/")
def home():
    # Renderizamos la plantilla HTML y le pasamos los datos de contacto y los packs.
    # Flask buscará 'index.html' automáticamente en la carpeta 'templates'.
    return render_template(
        'index.html', 
        contact=CONTACT_DATA, 
        packs=SERVICE_PACKS
    )

# Esta ruta NO es para visitar, es un "endpoint" al que el formulario envía los datos.
@app.route("/enviar-formulario", methods=["POST"])
def enviar_formulario():
    # El método es "POST" porque estamos recibiendo datos, no mostrándolos.
    
    # Recogemos los datos del formulario usando sus nombres ('name').
    nombre = request.form.get("nombre")
    apellidos = request.form.get("apellidos")
    email = request.form.get("email")
    pack_interes = request.form.get("pack_interes")
    notas = request.form.get("notas")

    # --- SIMULACIÓN DE ENVÍO DE EMAIL ---
    # Por ahora, para probar que todo funciona, imprimimos los datos en la consola
    # donde ejecutas `python app.py`.
    # El siguiente paso sería integrar aquí una librería para enviar emails reales.
    print("="*30)
    print("NUEVO CONTACTO RECIBIDO DESDE LA WEB")
    print(f"Nombre: {nombre} {apellidos}")
    print(f"Email: {email}")
    print(f"Pack de interés: {pack_interes}")
    print(f"Notas: {notas}")
    print("="*30)
    
    # Creamos un mensaje "flash" de éxito para mostrar al usuario.
    flash("¡Gracias por tu mensaje! Te contactaré muy pronto.", "success")
    
    # Redirigimos al usuario de vuelta a la página de inicio, pero a la sección de contacto.
    return redirect(url_for('home') + '#contacto')

# Esta línea permite ejecutar el servidor con el comando `python app.py`
if __name__ == "__main__":
    app.run(debug=True)