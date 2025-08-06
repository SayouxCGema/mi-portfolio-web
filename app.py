# ==========================================================
# app.py - Versión Final con Internacionalización (CORREGIDO)
# ==========================================================

# --- 1. IMPORTACIONES ---
import os
import resend
import json
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

@app.route("/enviar-mensaje", methods=["POST"])
def enviar_mensaje():
    lang = request.form.get('lang_code', 'es')
    # ... tu código de envío de email con Resend ...
    # (El resto de esta función no necesita cambios)
    nombre = request.form.get("nombre")
    apellidos = request.form.get("apellidos")
    email_cliente = request.form.get("email")
    pack_interes = request.form.get("pack_interes")
    notas = request.form.get("notas")
    resend.api_key = os.environ.get('RESEND_API_KEY')
    contenido_html = f"""
        <h3>Nuevo Contacto desde tu Portafolio Web</h3>
        <p><strong>Nombre:</strong> {nombre} {apellidos}</p>
        <p><strong>Email del Cliente:</strong> <a href="mailto:{email_cliente}">{email_cliente}</a></p>
        <p><strong>Servicio de Interés:</strong> {pack_interes}</p>
        <hr><p><strong>Mensaje:</strong></p><p>{notas}</p>
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
        print("INTENTO DE ENVÍO DE EMAIL CON RESEND - ÉXITO")
    except Exception as e:
        print(f"ERROR AL ENVIAR EMAIL CON RESEND: {e}")
    return redirect(url_for('pagina_gracias', lang_code=lang))

@app.route('/<lang_code>/gracias')
def pagina_gracias():
    return render_template('gracias.html')

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