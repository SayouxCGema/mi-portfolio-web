# ==========================================================
# app.py - Versión Final
# ==========================================================

# --- 1. IMPORTACIONES ---
# Todas las importaciones van juntas al principio.
import os
import resend
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, make_response

# --- 2. INICIALIZACIÓN DE LA APLICACIÓN ---
app = Flask(__name__)
app.secret_key = 'gema-calderon-sayoux-web-secreta' # Útil para futuras funcionalidades

# --- 3. DATOS GLOBALES DE LA APLICACIÓN ---

CONTACT_DATA = {
    "email": "gemacalderonsayoux@gmail.com",
    "linkedin": "https://www.linkedin.com/in/gema-calderon-sayoux/"
}

SERVICE_PACKS = [
    "Web completa (WordPress o HTML)",
    "Campañas Google Ads + Analytics",
    "Estrategia de contenidos SEO",
    "Pack de horas (5h, 10h o 20h)",
    "Consulta inicial (1h)",
    "No estoy seguro/a, necesito asesoramiento"
]

CASOS_DE_ESTUDIO_DB = {
    "aumento-visibilidad-katarsia": {
        "titulo": "1º puesto en Google para clínica en Barcelona: Tratamiento Sueroterapia",
        "cliente": "Centro Médico Katarsia",
        "problema": "Mejorar la venta de este tratamiento el cual tenía bastante margen de beneficio.",
        "solucion": "Se desarrolló contenido informativo sobre los diferentes tipos de compuestos de la Sueroterapia y se realizó un análisis del mercado en Estados Unidos para adaptarlo al mercado español.",
        "resultado": "Logramos un aumento del 564% en tráfico orgánico en 3 meses y un incremento del 45% en ventas atribuidas directamente a la búsqueda orgánica en un mes.",
        "imagenes": [
            "impresiones_katarsia.jpg", 
            "incremento_ingresos_katarsia.jpg"
        ]
    },
    "seo-local-macan": {
        "titulo": "Mejora de Posicionamiento Orgánico para Despacho de Abogados",
        "cliente": "Macan Abogados",
        "problema": "El despacho de abogados necesitaba mejorar su visibilidad en Google para captar nuevos clientes.",
        "solucion": "Después de realizar una auditoría técnica, se mejoraron las etiquetas, se incluyeron palabras clave de la competencia y se optimizó la estructura de la web.",
        "resultado": "Como resultado del trabajo realizado, se aumentó la visibilidad orgánica en un 466% y se mejoró la posición en los resultados de búsqueda (SERP), lo que incrementó el número de clics en un 249%.",
        "imagenes": [
            "macan_impresiones.jpg"
        ]
    }
}

# --- 4. RUTAS DE LA APLICACIÓN ---

@app.route("/")
def home():
    return render_template(
        'index.html', 
        contact=CONTACT_DATA, 
        packs=SERVICE_PACKS,
        casos_de_estudio=CASOS_DE_ESTUDIO_DB
    )

@app.route("/casos-de-estudio/<slug>")
def caso_de_estudio(slug):
    caso = CASOS_DE_ESTUDIO_DB.get(slug)
    if not caso:
        return "Caso de estudio no encontrado", 404
    return render_template('caso_de_estudio.html', caso=caso)

@app.route("/enviar-mensaje", methods=["POST"])
def enviar_mensaje():
    # Recogemos datos del formulario
    nombre = request.form.get("nombre")
    apellidos = request.form.get("apellidos")
    email_cliente = request.form.get("email")
    pack_interes = request.form.get("pack_interes")
    notas = request.form.get("notas")

    # Inicializamos Resend con la API Key de las variables de entorno
    resend.api_key = os.environ.get('RESEND_API_KEY')

    # Construimos el contenido del email
    contenido_html = f"""
        <h3>Nuevo Contacto desde tu Portafolio Web</h3>
        <p><strong>Nombre:</strong> {nombre} {apellidos}</p>
        <p><strong>Email del Cliente:</strong> <a href="mailto:{email_cliente}">{email_cliente}</a></p>
        <p><strong>Servicio de Interés:</strong> {pack_interes}</p>
        <hr>
        <p><strong>Mensaje:</strong></p>
        <p>{notas}</p>
    """

    try:
        params = {
            "from": "Contacto Web <contacto@gemacalderonsayoux.com>",
            "to": ["gemacalderonsayoux@gmail.com"],
            "subject": f"Nuevo mensaje de {nombre} sobre {pack_interes}",
            "html": contenido_html,
            "reply_to": email_cliente
        }
        email_enviado = resend.Emails.send(params)
        print("="*30)
        print("INTENTO DE ENVÍO DE EMAIL CON RESEND - ÉXITO")
        print(email_enviado)
        print("="*30)
    except Exception as e:
        print("="*30)
        print("ERROR AL ENVIAR EMAIL CON RESEND")
        print(e)
        print("="*30)

    return redirect(url_for('pagina_gracias'))

@app.route("/gracias")
def pagina_gracias():
    return render_template('gracias.html')


# --- 5. RUTAS PARA SEO ---

@app.route('/robots.txt')
def robots_txt():
    # Asumiendo que tienes un robots.txt en tu carpeta 'static'
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    # (CORREGIDO) La URL base debe ser la URL completa
    URL_BASE = "https://gemacalderonsayoux.com" 

    template = render_template('sitemap.xml', base_url=URL_BASE, casos_de_estudio=CASOS_DE_ESTUDIO_DB)
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response

# --- 6. ARRANQUE DE LA APLICACIÓN ---

if __name__ == "__main__":
    # Esto es para ejecutar la app en tu ordenador local con `python app.py`
    app.run(debug=True)