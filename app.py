# ==========================================================
# app.py - Versión Final, Completa y Funcional
# ==========================================================

import os
import json
import resend
import requests
import markdown
import yaml
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
    """Determina qué idioma usar para la petición actual."""
    # El idioma se obtiene del prefijo de la URL (ej: /en/), que Flask guarda en g.lang_code
    return getattr(g, 'lang_code', app.config['BABEL_DEFAULT_LOCALE'])

babel = Babel(app, locale_selector=get_locale)

# --- 2. MANEJO DE DATOS Y CONTEXTO ---

def load_lang_data(lang):
    """Carga los datos de casos de estudio, etc., desde el JSON del idioma."""
    path = os.path.join(app.root_path, 'translations', lang, 'data.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Si el archivo del idioma no existe, usa español como fallback.
        path_es = os.path.join(app.root_path, 'translations', 'es', 'data.json')
        with open(path_es, 'r', encoding='utf-8') as f:
            return json.load(f)

def load_blog_posts(lang):
    """Carga y procesa todos los posts del blog desde archivos Markdown."""
    posts = []
    dir_path = os.path.join(app.root_path, 'posts', lang)
    if not os.path.isdir(dir_path):
        # Si el directorio del idioma no existe, intenta con el de español como fallback
        dir_path = os.path.join(app.root_path, 'posts', 'es')
        if not os.path.isdir(dir_path):
            return []

    for filename in os.listdir(dir_path):
        if filename.endswith('.md'):
            path = os.path.join(dir_path, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content_parts = f.read().split('---', 2)
                if len(content_parts) >= 3:
                    metadata = yaml.safe_load(content_parts[1])
                    content_md = content_parts[2]
                    metadata['content'] = markdown.markdown(content_md)
                    posts.append(metadata)
    
    posts.sort(key=itemgetter('date'), reverse=True)
    return posts

@app.url_value_preprocessor
def pull_lang_code(endpoint, values):
    """Obtiene el código de idioma de la URL antes 