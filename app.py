# app.py - Versión Actualizada
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, make_response

app = Flask(__name__)
# La 'secret_key' sigue siendo útil si en el futuro quieres usar mensajes flash en otras partes.
app.secret_key = 'gema-calderon-sayoux-web-secreta'

# --- DATOS GLOBALES DE LA APLICACIÓN ---

# Datos de contacto (sin cambios)
CONTACT_DATA = {
    "email": "gemacalderonsayoux@gmail.com",
    "linkedin": "https://www.linkedin.com/in/gema-calderon-sayoux/"
}

# Packs de servicios para el formulario (sin cambios)
SERVICE_PACKS = [
    "Web completa (WordPress o HTML)",
    "Campañas Google Ads + Analytics",
    "Estrategia de contenidos SEO",
    "Pack de horas (5h, 10h o 20h)",
    "Consulta inicial (1h)",
    "No estoy seguro/a, necesito asesoramiento"
]

# (NUEVO) Base de datos simulada para Casos de Estudio.
# La "clave" (ej: "aumento-visibilidad-ecommerce") será parte de la URL, por eso no lleva espacios ni tildes.
CASOS_DE_ESTUDIO_DB = {
    "aumento-visibilidad-katarsia": {
        "titulo": "1º puesto en Google para clínica en Barcelona tratamiento Sueroterapia",
        "cliente": "Centro Médico Katarsia",
        "problema": "Mejorar la venta de este tratamiento el cual tenía bastante margen de beneficio",
        "solucion": "Se desarrolló contenido informativo, sobre los diferentes tipos de compuestos de la Sueroterapia, análisis del mercado en Estados Unidos(para adaptarlo al mercado Español",
        "resultado": "Logramos un aumento del 564% en tráfico orgánico en 3 meses y un incremento del 45% en ventas atribuidas directamente a la búsqueda orgánica en un mes.",
        "imagen_principal": "impresiones_katarsia.jpg" # Nombre del archivo en static/img/
        "imagen_principal": "incremento_ingresos_katarsia.jpg" # Nombre del archivo en static/img/
    },
    "seo-local-macan": {
        "titulo": "Mejorar posicionamiento orgánico'",
        "cliente": "Macan Abogados'",
        "problema": "El despacho de abogados, necesitaba mejorar la visibilidad en Google",
        "solucion": "Después de realizar una auditoría técnica, se mejoraron las etiquetas y se incluyeron palabras claves que usaba la competencia, además de mejorar la estructura de la web",
        "resultado": "Como resultado del trabajo realizado se aumento la visibilidad orgánica en un 466%, además de mejorar la posición en los resultados de la SERP lo que aumento el número de clics en un 249%.",
        "imagen_principal": "macan_impresiones.jpg"
    }
}

# --- RUTAS DE LA APLICACIÓN ---

@app.route("/")
def home():
    # Ahora, además de los datos de contacto y packs, pasamos los casos de estudio.
    return render_template(
        'index.html', 
        contact=CONTACT_DATA, 
        packs=SERVICE_PACKS,
        casos_de_estudio=CASOS_DE_ESTUDIO_DB # Pasamos el diccionario a la plantilla
    )

# (NUEVO) Ruta dinámica para mostrar cada caso de estudio individualmente.
# El <slug> se corresponderá con las claves del diccionario CASOS_DE_ESTUDIO_DB.
@app.route("/casos-de-estudio/<slug>")
def caso_de_estudio(slug):
    caso = CASOS_DE_ESTUDIO_DB.get(slug)
    # Si alguien intenta acceder a una URL de un caso que no existe, mostramos un error.
    if not caso:
        return "Caso de estudio no encontrado", 404
    # Renderizamos una nueva plantilla específica para los casos de estudio.
    return render_template('caso_de_estudio.html', caso=caso)


# (MODIFICADO) La ruta del formulario ahora redirige a una página de "gracias".
# He cambiado el nombre de la ruta a 'enviar_mensaje' por ser más descriptivo.
# ¡Recuerda actualizar el 'action' de tu formulario en index.html!
@app.route("/enviar-mensaje", methods=["POST"])
def enviar_mensaje():
    nombre = request.form.get("nombre")
    email = request.form.get("email")
    # ... recoge los demás campos que necesites ...
    
    # La lógica de simulación de envío sigue siendo útil para depurar.
    print("="*30)
    print("NUEVO CONTACTO RECIBIDO DESDE LA WEB")
    print(f"Nombre: {nombre}")
    print(f"Email: {email}")
    print("="*30)
    
    # En lugar de un mensaje flash, redirigimos a la nueva página de agradecimiento.
    return redirect(url_for('pagina_gracias'))

# (NUEVO) Ruta para la página de agradecimiento.
@app.route("/gracias")
def pagina_gracias():
    return render_template('gracias.html')


# --- RUTAS PARA SEO ---

# (NUEVO) Ruta para servir el archivo robots.txt desde la carpeta 'static'.
@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')

# (NUEVO) Ruta para generar el sitemap.xml dinámicamente.
@app.route('/sitemap.xml')
def sitemap():
    # ¡IMPORTANTE! Cambia esta URL por tu dominio cuando lo tengas.
    URL_BASE = "gemacalderonsayoux.com" 

    # Renderizamos una plantilla XML, pasándole los datos necesarios para crear las URLs.
    template = render_template('sitemap.xml', base_url=URL_BASE, casos_de_estudio=CASOS_DE_ESTUDIO_DB)
    # Creamos una respuesta HTTP y le asignamos el tipo de contenido correcto.
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response


# Esta línea no cambia.
if __name__ == "__main__":
    app.run(debug=True)