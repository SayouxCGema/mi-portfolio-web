# ==========================================================
# app.py - Versión Final con Internacionalización (CORREGIDO)
# ==========================================================

# --- 1. IMPORTACIONES ---
import os
import resend
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, g, make_response, send_from_directory
from flask_babel import Babel

# --- 2. INICIALIZACIÓN DE LA APLICACIÓN ---
app = Flask(__name__)
app.secret_key = 'gema-calderon-sayoux-web-secreta'

# --- 3. MANEJO DEL IDIOMA (SINTAXIS MODERNA) ---

# Primero, definimos la función que seleccionará el idioma
def get_locale():
    # getattr es una forma segura de obtener g.lang_code, por si no existiera
    return getattr(g, 'lang_code', app.config['BABEL_DEFAULT_LOCALE'])

# Ahora, configuramos Babel y le pasamos la función directamente
app.config['LANGUAGES'] = {'es': 'Español', 'en': 'English'}
app.config['BABEL_DEFAULT_LOCALE'] = 'es'
babel = Babel(app, locale_selector=get_locale)

# Esta función carga los datos del archivo JSON correspondiente al idioma actual
def load_lang_data(lang):
    try:
        with open(f'translations/{lang}/data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        with open('translations/es/data.json', 'r', encoding='utf-8') as f:
            return json.load(f)

# Esta función se ejecuta antes de cada petición para determinar el idioma
@app.url_value_preprocessor
def pull_lang_code(endpoint, values):
    if values is not None:
        g.lang_code = values.pop('lang_code', app.config['BABEL_DEFAULT_LOCALE'])
    else:
        g.lang_code = app.config['BABEL_DEFAULT_LOCALE']

# Esta función hace que el idioma esté disponible para todas las plantillas
@app.context_processor
def inject_lang_code():
    return dict(lang_code=getattr(g, 'lang_code', app.config['BABEL_DEFAULT_LOCALE']))

# --- 4. DATOS GLOBALES (QUE NO SE TRADUCEN) ---
CONTACT_DATA = {
    "email": "gemacalderonsayoux@gmail.com",
    "linkedin": "https://www.linkedin.com/in/gema-calderon-sayoux/"
}
SERVICE_PACKS = [
    "Web completa (WordPress o HTML + SEO básico)", "Campañas Google Ads + Analytics",
    "Estrategia de contenidos SEO", "Pack de horas (5h, 10h o 20h)",
    "Consulta inicial (1h)", "No estoy seguro/a, necesito asesoramiento"
]

# --- 5. RUTAS DE LA APLICACIÓN ---
@app.route('/')
def home_redirect():
    return redirect(url_for('home', lang_code='es'))

@app.route('/<lang_code>/')
def home():
    page_data = load_lang_data(g.lang_code)
    return render_template('index.html', contact=CONTACT_DATA, packs=SERVICE_PACKS, casos_de_estudio=page_data.get('casos_de_estudio', {}))

@app.route('/<lang_code>/casos-de-estudio/<slug>')
def caso_de_estudio(slug):
    page_data = load_lang_data(g.lang_code)
    caso = page_data.get('casos_de_estudio', {}).get(slug)
    if not caso:
        return "Caso de estudio no encontrado", 404
    return render_template('caso_de_estudio.html', caso=caso)

# app.py (función enviar_mensaje final y correcta)

# Asegúrate de tener 'import requests' al principio de tu app.py
import requests

@app.route("/enviar-mensaje", methods=["POST"])
def enviar_mensaje():
    # --- 1. Verificación de reCAPTCHA ---
    recaptcha_token = request.form.get('g-recaptcha-response')
    secret_key = os.environ.get('RECAPTCHA_SECRET_KEY')
    
    # Si la clave secreta no está configurada, no podemos verificar. Fallamos silenciosamente.
    if not secret_key:
        print("ERROR: La clave secreta de reCAPTCHA no está configurada en las variables de entorno.")
        return redirect(url_for('pagina_gracias'))

    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    payload = {
        'secret': secret_key,
        'response': recaptcha_token
    }
    
    try:
        response = requests.post(verify_url, data=payload)
        result = response.json()
        
        # Si la verificación falla o la puntuación es muy baja (es un bot), redirigimos y no enviamos email.
        if not result.get('success') or result.get('score', 0) < 0.5:
            print(f"SPAM DETECTADO por reCAPTCHA: Puntuación de {result.get('score', 0)}")
            return redirect(url_for('pagina_gracias'))
    except Exception as e:
        print(f"Error al verificar reCAPTCHA: {e}")
        # En caso de error, no enviamos el email por seguridad.
        return redirect(url_for('pagina_gracias'))
        
    # --- 2. Si pasa la verificación, recogemos datos y enviamos el email ---
    
    # Recogemos los datos del formulario (una sola vez)
    nombre = request.form.get("nombre")
    apellidos = request.form.get("apellidos")
    email_cliente = request.form.get("email")
    pack_interes = request.form.get("pack_interes")
    notas = request.form.get("notas")
    
    # Inicializamos Resend con la API Key
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
    
    # Intentamos enviar el email
    try:
        params = {
            "from": "Contacto Web <contacto@gemacalderonsayoux.com>",
            "to": ["gemacalderonsayoux@gmail.com"],
            "subject": f"Nuevo mensaje de {nombre} sobre {pack_interes}",
            "html": contenido_html,
            "reply_to": email_cliente
        }
        email_enviado = resend.Emails.send(params)
        print("INTENTO DE ENVÍO DE EMAIL CON RESEND - ÉXITO")
    except Exception as e:
        print(f"ERROR AL ENVIAR EMAIL CON RESEND: {e}")
        
    # --- 3. Finalmente, redirigimos a la página de gracias ---
    return redirect(url_for('pagina_gracias'))

# --- 6. RUTAS PARA SEO ---
@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')

# --- AÑADE ESTA NUEVA RUTA AQUÍ ABAJO ---
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'favicons'), 
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.route('/sitemap.xml')
def sitemap():
    URL_BASE = "https://gemacalderonsayoux.com"
    page_data_es = load_lang_data('es')
    casos_es = page_data_es.get('casos_de_estudio', {})
    template = render_template('sitemap.xml', base_url=URL_BASE, casos_de_estudio=casos_es)
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response

# --- 7. ARRANQUE DE LA APLICACIÓN ---
if __name__ == "__main__":
    app.run(debug=True)