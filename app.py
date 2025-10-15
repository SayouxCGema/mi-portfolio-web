# ==========================================================
# app.py - Versión Final, Unificada y Robusta
# ==========================================================

import os
import json
import resend
import requests
import yaml
import markdown
from operator import itemgetter
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, g, make_response, send_from_directory
from flask_babel import Babel, _

# --- 1. CONFIGURACIÓN DE LA APP Y EXTENSIONES ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'una-clave-secreta-larga-y-aleatoria-por-defecto')

# Configuración de Babel para internacionalización
app.config['LANGUAGES'] = {'es': 'Español', 'en': 'English'}
app.config['BABEL_DEFAULT_LOCALE'] = 'es'

def get_locale():
    """Determina qué idioma usar para la petición actual, basándose en la variable 'g'."""
    return getattr(g, 'lang_code', app.config['BABEL_DEFAULT_LOCALE'])

babel = Babel(app, locale_selector=get_locale)

# --- 2. FUNCIONES AUXILIARES DE CARGA DE DATOS ---

def load_lang_data(lang):
    """Carga datos de casos de estudio y servicios desde un archivo JSON."""
    path = os.path.join(app.root_path, 'translations', lang, 'data.json')
    try:
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        path_fallback = os.path.join(app.root_path, 'translations', 'es', 'data.json')
        with open(path_fallback, 'r', encoding='utf-8') as f: return json.load(f)

def load_blog_posts(lang):
    """Carga y procesa todos los posts del blog desde archivos Markdown."""
    posts, dir_path = [], os.path.join(app.root_path, 'posts', lang)
    if not os.path.isdir(dir_path):
        dir_path_fallback = os.path.join(app.root_path, 'posts', 'es')
        if not os.path.isdir(dir_path_fallback): return []
        dir_path = dir_path_fallback
    for filename in os.listdir(dir_path):
        if filename.endswith('.md'):
            with open(os.path.join(dir_path, filename), 'r', encoding='utf-8') as f:
                content_parts = f.read().split('---', 2)
                if len(content_parts) >= 3:
                    try:
                        metadata = yaml.safe_load(content_parts[1])
                        if 'date' in metadata and isinstance(metadata['date'], str):
                            metadata['date'] = datetime.strptime(metadata['date'], '%Y-%m-%d')
                        metadata['content'] = markdown.markdown(content_parts[2], extensions=['fenced_code', 'tables'])
                        posts.append(metadata)
                    except yaml.YAMLError as e:
                        print(f"ERROR AL LEER YAML en el archivo {filename}: {e}")
    posts.sort(key=itemgetter('date'), reverse=True)
    return posts

# --- 3. HOOKS DE PETICIÓN Y PROCESADORES DE CONTEXTO ---

@app.before_request
def before_request():
    """Se ejecuta antes de CADA petición. Define el idioma y carga todos los datos necesarios."""
    lang_code_from_url = request.view_args.get('lang_code') if request.view_args else None
    if lang_code_from_url and lang_code_from_url in app.config['LANGUAGES']:
        g.lang_code = lang_code_from_url
    else:
        g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'es'
    g.lang_data = load_lang_data(g.lang_code)
    # NOTA: Cargamos los posts del idioma actual aquí. La ruta del blog los usará.
    g.posts = load_blog_posts(g.lang_code)

@app.context_processor
def inject_global_vars():
    """Hace que ciertas variables estén disponibles en TODAS las plantillas."""
    return dict(
        g=g,
        contact={'email': os.environ.get('CONTACT_EMAIL'), 'linkedin': os.environ.get('LINKEDIN_URL')},
        recaptcha_site_key=os.environ.get('RECAPTCHA_SITE_KEY'),
        current_year=datetime.utcnow().year,
        GA_MEASUREMENT_ID=os.environ.get('GA_MEASUREMENT_ID'),
        packs=g.lang_data.get('service_packs', {}),
        languages=app.config['LANGUAGES']
    )

# --- 4. RUTAS PRINCIPALES DE LA APLICACIÓN ---

@app.route('/')
def home_redirect():
    detected_lang = request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'es'
    return redirect(url_for('home', lang_code=detected_lang))

@app.route('/<lang_code>/')
def home(lang_code):
    return render_template('index.html', casos_de_estudio=g.lang_data.get('casos_de_estudio', {}))

@app.route('/<lang_code>/casos-de-estudio/<slug>')
def caso_de_estudio(lang_code, slug):
    caso = g.lang_data.get('casos_de_estudio', {}).get(slug)
    if not caso: return _("Caso de estudio no encontrado"), 404
    return render_template('caso_de_estudio.html', caso=caso)

@app.route('/<lang_code>/servicios/<slug>')
def servicio_detalle(lang_code, slug):
    servicio = g.lang_data.get('servicios_detalle', {}).get(slug)
    if not servicio: return redirect(url_for('home', lang_code=lang_code, _anchor='servicios'))
    
    alternate_url = None
    translation_key = servicio.get('translation_key')
    if translation_key:
        alternate_lang = 'en' if lang_code == 'es' else 'es'
        alternate_data = load_lang_data(alternate_lang).get('servicios_detalle', {})
        for alt_slug, alt_item in alternate_data.items():
            if alt_item.get('translation_key') == translation_key:
                alternate_url = url_for('servicio_detalle', lang_code=alternate_lang, slug=alt_slug)
                break
                
    return render_template('servicio_detalle.html', servicio=servicio, alternate_url=alternate_url)

@app.route('/<lang_code>/blog/')
def blog_index(lang_code):
    return render_template('blog.html', posts=g.posts)

# (VERSIÓN ÚNICA Y DEFINITIVA) RUTA DEL BLOG POST CON LÓGICA DE REDIRECCIÓN INTEGRADA
@app.route('/<lang_code>/blog/<slug>')
def blog_post(lang_code, slug):
    # g.posts ya contiene los posts del idioma correcto (ej: 'en') gracias a before_request
    post = next((p for p in g.posts if p.get('slug') == slug), None)

    if post:
        # ¡ÉXITO! Se encontró el post. Ahora busca su traducción para el selector de idioma.
        alternate_url = None
        translation_key = post.get('translation_key')
        if translation_key:
            alternate_lang = 'en' if lang_code == 'es' else 'es'
            alternate_posts = load_blog_posts(alternate_lang)
            alternate_post = next((p for p in alternate_posts if p.get('translation_key') == translation_key), None)
            if alternate_post:
                alternate_url = url_for('blog_post', lang_code=alternate_lang, slug=alternate_post.get('slug'))
        
        return render_template('post.html', post=post, alternate_url=alternate_url)
    
    # FALLO: No se encontró el post en el idioma actual.
    # Ahora comprobamos si es un slug en el idioma incorrecto para hacer una redirección 301.
    if lang_code == 'en':
        # El usuario está en /en/, pero el slug no se encontró. ¿Quizás es un slug en español?
        posts_es = load_blog_posts('es')
        post_es = next((p for p in posts_es if p.get('slug') == slug), None)
        
        if post_es and 'translation_key' in post_es:
            # Encontramos un post en ESPAÑOL con este slug. Buscamos su traducción en INGLÉS.
            translation_key = post_es['translation_key']
            posts_en = load_blog_posts('en')
            post_en_correspondiente = next((p for p in posts_en if p.get('translation_key') == translation_key), None)
            
            if post_en_correspondiente and 'slug' in post_en_correspondiente:
                # ¡Lo encontramos! Redirigimos permanentemente a la URL inglesa correcta.
                correct_url = url_for('blog_post', lang_code='en', slug=post_en_correspondiente['slug'])
                return redirect(correct_url, code=301)
    
    # Si nada de lo anterior funciona, es un 404 definitivo.
    return _("Post no encontrado"), 404

@app.route('/<lang_code>/gracias')
def pagina_gracias(lang_code):
    return render_template('gracias.html')

@app.route('/enviar-mensaje', methods=['POST'])
def enviar_mensaje():
    lang_code = request.form.get('lang_code', 'es')
    
    # Lógica de reCAPTCHA
    recaptcha_token = request.form.get('g-recaptcha-response')
    secret_key = os.environ.get('RECAPTCHA_SECRET_KEY')
    if not recaptcha_token or not secret_key:
        print("ERROR: Token o clave secreta de reCAPTCHA faltantes.")
        return redirect(url_for('pagina_gracias', lang_code=lang_code))
    try:
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data={'secret': secret_key, 'response': recaptcha_token})
        result = response.json()
        if not result.get('success') or result.get('score', 0) < 0.5:
            print(f"SPAM DETECTADO por reCAPTCHA: Puntuación de {result.get('score', 0)}")
            return redirect(url_for('pagina_gracias', lang_code=lang_code))
    except Exception as e:
        print(f"Error al verificar reCAPTCHA: {e}")
        return redirect(url_for('pagina_gracias', lang_code=lang_code))

    # Lógica de envío de email con Resend
    nombre, apellidos, email_cliente, pack_interes, notas = request.form.get("nombre"), request.form.get("apellidos"), request.form.get("email"), request.form.get("pack_interes"), request.form.get("notas")
    try:
        resend.api_key = os.environ.get('RESEND_API_KEY')
        contenido_html = f"""<h3>Nuevo Contacto Web</h3><p><strong>Nombre:</strong> {nombre} {apellidos}</p><p><strong>Email:</strong> {email_cliente}</p><p><strong>Interés:</strong> {pack_interes}</p><hr><p><strong>Mensaje:</strong></p><p>{notas}</p>"""
        params = {"from": f"Contacto Web <contacto@{os.environ.get('MAIL_DOMAIN')}>", "to": [os.environ.get('CONTACT_EMAIL')], "subject": f"Nuevo mensaje de {nombre}", "html": contenido_html, "reply_to": email_cliente}
        resend.Emails.send(params)
        print("ÉXITO: Email enviado con Resend.")
    except Exception as e:
        print(f"ERROR AL ENVIAR EMAIL CON RESEND: {e}")
    
    return redirect(url_for('pagina_gracias', lang_code=lang_code))

# --- 5. RUTAS PARA SEO Y FAVICON ---
@app.route('/robots.txt')
def robots_txt(): return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/favicon.ico')
def favicon(): return send_from_directory(os.path.join(app.root_path, 'static', 'favicons'), 'favicon.ico')

@app.route('/sitemap.xml')
def sitemap():
    URL_BASE = "https://gemacalderonsayoux.com"
    casos_es = load_lang_data('es').get('casos_de_estudio', {})
    posts_es = load_blog_posts('es')
    template = render_template('sitemap.xml', base_url=URL_BASE, casos_de_estudio=casos_es, posts=posts_es)
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response

# --- 6. ARRANQUE DE LA APLICACIÓN ---
if __name__ == "__main__":
    app.run(debug=True)