# ==========================================================
# app.py - Versión Final, Robusta y Simplificada
# ==========================================================

import os
import json
import resend
import requests
import yaml
import markdown
from operator import itemgetter
from flask import Flask, render_template, request, redirect, url_for, g, make_response, send_from_directory
from flask_babel import Babel, _

# --- 1. CONFIGURACIÓN DE LA APP Y EXTENSIONES ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'una-clave-secreta-larga-y-aleatoria-por-defecto')

# Configuración de Babel para internacionalización
app.config['LANGUAGES'] = {'es': 'Español', 'en': 'English'}
app.config['BABEL_DEFAULT_LOCALE'] = 'es'

@babel.localeselector
def get_locale():
    """Determina qué idioma usar para la petición actual, basándose en la variable 'g'."""
    return getattr(g, 'lang_code', app.config['BABEL_DEFAULT_LOCALE'])

babel = Babel(app, locale_selector=get_locale)

# --- 2. MANEJO DE DATOS Y CONTEXTO (LÓGICA UNIFICADA) ---

def load_lang_data(lang):
    """Carga datos de casos de estudio y servicios desde un archivo JSON."""
    path = os.path.join(app.root_path, 'translations', lang, 'data.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Si el archivo del idioma actual falla, carga el de español como fallback
        path_fallback = os.path.join(app.root_path, 'translations', 'es', 'data.json')
        with open(path_fallback, 'r', encoding='utf-8') as f:
            return json.load(f)

def load_blog_posts(lang):
    """Carga y procesa todos los posts del blog desde archivos Markdown."""
    posts = []
    dir_path = os.path.join(app.root_path, 'posts', lang)
    if not os.path.isdir(dir_path):
        dir_path_fallback = os.path.join(app.root_path, 'posts', 'es')
        if not os.path.isdir(dir_path_fallback): return []
        dir_path = dir_path_fallback

    for filename in os.listdir(dir_path):
        if filename.endswith('.md'):
            path = os.path.join(dir_path, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content_parts = f.read().split('---', 2)
                if len(content_parts) >= 3:
                    metadata = yaml.safe_load(content_parts[1])
                    content_md = content_parts[2]
                    metadata['content'] = markdown.markdown(content_md, extensions=['fenced_code', 'tables'])
                    posts.append(metadata)
    
    posts.sort(key=itemgetter('date'), reverse=True)
    return posts

@app.before_request
def before_request():
    """Se ejecuta antes de CADA petición. Define el idioma y carga todos los datos necesarios."""
    # Elimina la necesidad de @app.url_value_preprocessor, simplificando la lógica.
    lang_code_from_url = request.view_args.get('lang_code') if request.view_args else None
    if lang_code_from_url and lang_code_from_url in app.config['LANGUAGES']:
        g.lang_code = lang_code_from_url
    else:
        g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'es'
    
    # Carga los datos una sola vez por petición y los guarda en 'g'
    g.lang_data = load_lang_data(g.lang_code)
    g.posts = load_blog_posts(g.lang_code)

@app.context_processor
def inject_global_vars():
    """Hace que ciertas variables estén disponibles en TODAS las plantillas."""
    return dict(
        g=g, # Pasa el objeto 'g' completo a las plantillas
        contact={'email': os.environ.get('CONTACT_EMAIL'), 'linkedin': os.environ.get('LINKEDIN_URL')},
        recaptcha_site_key=os.environ.get('RECAPTCHA_SITE_KEY')
    )

# --- 3. RUTAS DE LA APLICACIÓN (SIMPLIFICADAS Y CORREGIDAS) ---

@app.route('/')
def home_redirect():
    """Redirige la raíz (/) a la versión con el idioma detectado."""
    detected_lang = request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'es'
    return redirect(url_for('home', lang_code=detected_lang))

# (CORREGIDO) La función ahora SÍ acepta 'lang_code' para coincidir con la ruta
@app.route('/<lang_code>/')
def home(lang_code):
    return render_template('index.html',
                           packs=g.lang_data.get('service_packs', []),
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
    # Tu lógica de reCAPTCHA y envío de email aquí... (sin cambios)
    # ...
    return redirect(url_for('pagina_gracias', lang_code=request.form.get('lang_code', 'es')))


# --- 4. RUTAS PARA SEO Y FAVICON --- (Sin cambios)
@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'favicons'), 'favicon.ico')

@app.route('/sitemap.xml')
def sitemap():
    URL_BASE = "https://gemacalderonsayoux.com"
    casos_es = load_lang_data('es').get('casos_de_estudio', {})
    posts_es = load_blog_posts('es')
    template = render_template('sitemap.xml', base_url=URL_BASE, casos_de_estudio=casos_es, posts=posts_es)
    response = make_response(template)
    response.headers['Content-Type'] = 'application/xml'
    return response

# --- 5. ARRANQUE DE LA APLICACIÓN ---
if __name__ == "__main__":
    app.run(debug=True)