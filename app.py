# ==========================================================
# app.py - Versión Final, Robusta y Corregida
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

# --- 1. CONFIGURACIÓN DE LA APP ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'una-clave-secreta-larga-y-aleatoria-por-defecto')

# --- 2. CONFIGURACIÓN DE BABEL (INTERNACIONALIZACIÓN) - FORMA CORRECTA ---
app.config['LANGUAGES'] = {'es': 'Español', 'en': 'English'}
app.config['BABEL_DEFAULT_LOCALE'] = 'es'

# (CORRECCIÓN #1 - SOLUCIONA EL NameError)
# Primero se define la función que seleccionará el idioma.
def get_locale():
    """Determina qué idioma usar para la petición actual, basándose en la variable 'g'."""
    return getattr(g, 'lang_code', app.config['BABEL_DEFAULT_LOCALE'])

# Y LUEGO se crea el objeto Babel, pasándole la función.
# Esto es más limpio y seguro que usar el decorador @babel.localeselector.
babel = Babel(app, locale_selector=get_locale)

# --- 3. MANEJO DE DATOS Y CONTEXTO (LÓGICA UNIFICADA Y SIMPLIFICADA) ---

@app.before_request
def before_request():
    """
    Se ejecuta ANTES de cada petición.
    Define el idioma y carga todos los datos necesarios en la variable global 'g'.
    """
    # Se extrae el 'lang_code' de los argumentos de la URL (ej: /es/)
    lang_code_from_url = request.view_args.get('lang_code') if request.view_args else None
    
    if lang_code_from_url and lang_code_from_url in app.config['LANGUAGES']:
        g.lang_code = lang_code_from_url
    else:
        # Si no hay prefijo de idioma, se negocia con el navegador
        g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'es'
    
    # Carga los datos una sola vez por petición
    g.lang_data = load_lang_data(g.lang_code)
    g.posts = load_blog_posts(g.lang_code)

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
                    metadata = yaml.safe_load(content_parts[1])
                    metadata['content'] = markdown.markdown(content_parts[2], extensions=['fenced_code', 'tables'])
                    posts.append(metadata)
    posts.sort(key=itemgetter('date'), reverse=True)
    return posts

@app.context_processor
def inject_global_vars():
    """Hace que ciertas variables estén disponibles en TODAS las plantillas."""
    return dict(
        g=g,
        contact={'email': os.environ.get('CONTACT_EMAIL'), 'linkedin': os.environ.get('LINKEDIN_URL')},
        recaptcha_site_key=os.environ.get('RECAPTCHA_SITE_KEY')
    )

# --- 4. RUTAS DE LA APLICACIÓN (CORREGIDAS) ---

@app.route('/')
def home_redirect():
    """Redirige la raíz (/) a la versión con el idioma detectado."""
    detected_lang = request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or 'es'
    return redirect(url_for('home', lang_code=detected_lang))

# (CORRECCIÓN #2 - SOLUCIONA EL TypeError)
# La función ahora SÍ acepta 'lang_code' como argumento, coincidiendo con la ruta.
@app.route('/<lang_code>/')
def home(lang_code):
    return render_template('index.html',
                           packs=g.lang_data.get('service_packs', []),
                           casos_de_estudio=g.lang_data.get('casos_de_estudio', {}))

@app.route('/<lang_code>/casos-de-estudio/<slug>')
def caso_de_estudio(lang_code, slug):
    caso = g.lang_data.get('casos_de_estudio', {}).get(slug)
    if not caso: return _("Caso