# ==========================================================
# app.py - Versión Definitiva, Corregida y Verificada
# ==========================================================

import os
import json
import resend
import requests
import yaml
import markdown
from operator import itemgetter
from datetime import datetime # (NUEVO) Importamos el módulo datetime
from flask import Flask, render_template, request, redirect, url_for, g, make_response, send_from_directory
from flask_babel import Babel, _

# --- 1. CONFIGURACIÓN DE LA APP ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'una-clave-secreta-larga-y-aleatoria-por-defecto')

# --- 2. CONFIGURACIÓN DE BABEL (INTERNACIONALIZACIÓN) ---
app.config['LANGUAGES'] = {'es': 'Español', 'en': 'English'}
app.config['BABEL_DEFAULT_LOCALE'] = 'es'

def get_locale():
    """Determina qué idioma usar para la petición actual, basándose en la variable 'g'."""
    return getattr(g, 'lang_code', app.config['BABEL_DEFAULT_LOCALE'])

babel = Babel(app, locale_selector=get_locale)

# --- 3. MANEJO DE DATOS Y CONTEXTO ---

@app.before_request
def before_request():
    """Se ejecuta ANTES de cada petición para definir el idioma y cargar todos los datos."""
    lang_code_from_url = request.view_args.get('lang_code') if request.view_args else None
    if lang_code_from_url and lang_code_from_url in app.config['LANGUAGES']:
        g.lang_code = lang_code_from_url
    else:
        g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'es'
    
    g.lang_data = load_lang_data(g.lang_code)
    g.posts = load_blog_posts(g.lang_code)
    # (CORRECCIÓN FINAL) La información de contacto se adjunta a 'g' para estar disponible en todas las plantillas.
    g.contact = {'email': os.environ.get('CONTACT_EMAIL'), 'linkedin': os.environ.get('LINKEDIN_URL')}

def load_lang_data(lang):
    """Carga datos de casos de estudio, servicios, etc., desde un archivo JSON."""
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
                    metadata = yaml.safe_load(content_parts[1])
                    # (CORRECCIÓN) Convertimos el string de la fecha a un objeto datetime
                    # Esto asume que tus fechas en los archivos .md están en formato AÑO-MES-DÍA (ej: 2025-08-13)
                    if 'date' in metadata and isinstance(metadata['date'], str):
                        try:
                            metadata['date'] = datetime.strptime(metadata['date'], '%Y-%m-%d')
                        except ValueError:
                            # Si el formato es incorrecto, usa la fecha actual como fallback
                            metadata['date'] = datetime.now()
                    metadata['content'] = markdown.markdown(content_parts[2], extensions=['fenced_code', 'tables'])
                    posts.append(metadata)
    posts.sort(key=itemgetter('date'), reverse=True)
    return posts

@app.context_processor
def inject_global_vars():
    """Hace que ciertas variables estén disponibles en TODAS las plantillas."""
    return dict(
        g=g,
        recaptcha_site_key=os.environ.get('RECAPTCHA_SITE_KEY'),
        ga_measurement_id=os.environ.get('GA_MEASUREMENT_ID'),
        app=app
    )

# --- 4. RUTAS DE LA APLICACIÓN ---

@app.route('/')
def home_redirect():
    detected_lang = request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'es'
    return redirect(url_for('home', lang_code=detected_lang))

@app.route('/<lang_code>/')
def home(lang_code):
    return render_template('index.html',
                           packs=g.lang_data.get('service_packs', {}),
                           casos_de_estudio=g.lang_data.get('casos_de_estudio', {}))

@app.route('/<lang_code>/casos-de-estudio/<slug>')
def caso_de_estudio(lang_code, slug):
    caso = g.lang_data.get('casos_de_estudio', {}).get(slug)
    if not caso: 
        return _("Caso de estudio no encontrado"), 404
    return render_template('caso_de_estudio.html', caso=caso)

@app.route('/<lang_code>/blog/')
def blog_index(lang_code):
    return render_template('blog.html', posts=g.posts)

@app.route('/<lang_code>/blog/<slug>')
def blog_post(lang_code, slug):
    post = next((p for p in g.posts if p.get('slug') == slug), None)
    if not post: 
        return _("Post no encontrado"), 404
    return render_template('post.html', post=post)

@app.route('/<lang_code>/gracias')
def pagina_gracias(lang_code):
    return render_template('gracias.html')

@app.route('/enviar-mensaje', methods=['POST'])
def enviar_mensaje():
    lang_code = request.form.get('lang_code', 'es')
    # ... Tu lógica de reCAPTCHA y Resend ...
    # (Asegúrate de que esta parte está completa en tu archivo)
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