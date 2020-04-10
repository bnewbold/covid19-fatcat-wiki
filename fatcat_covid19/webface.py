
"""
This is the single-file Flask web application
"""

import os
import subprocess

from flask import Flask, Blueprint, g, app, render_template, request, send_from_directory
from flask_babel import Babel, gettext
from flask.logging import create_logger
import elasticsearch

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


class BaseConfig(object):

    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'de': 'Deutsch',
        'zh': '中文',
    }
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    GIT_REVISION = subprocess.check_output(["git", "describe", "--always"]).strip().decode('utf-8')

    ELASTICSEARCH_BACKEND = os.environ.get("ELASTICSEARCH_BACKEND", default="https://search.fatcat.wiki")
    ELASTICSEARCH_FULLTEXT_INDEX = os.environ.get("ELASTICSEARCH_FULLTEXT_INDEX", default="covid19_fatcat_fulltext")
    COVID19_FULLTEXT_HOST = os.environ.get("COVID19_FULLTEXT_HOST", default="https://covid19.fatcat.wiki")

    # this variable is vestigal, used in some jinja2 templates
    FATCAT_DOMAIN = "covid19.fatcat.wiki"

    SENTRY_CONFIG = {
        'enable-threads': True, # for uWSGI
        'release': GIT_REVISION,
        'tags': {
            'service': 'covid19.fatcat.wiki',
        },
    }

sentry_sdk.init(
    # set SDN via environment variable SENTRY_DSN
    integrations=[FlaskIntegration()]
)

app = Flask(__name__, static_url_path='/static')
app.config.from_object(BaseConfig())
app.log = create_logger(app)
babel = Babel(app)
app.es_client = elasticsearch.Elasticsearch(app.config['ELASTICSEARCH_BACKEND'])

# remove most jinja2 template whitespace
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

from fatcat_covid19.search import *

bp = Blueprint('search', __name__)

@bp.url_defaults
def add_language_code(endpoint, values):
    if hasattr(g, "lang_code_set") and g.lang_code_set:
        values.setdefault('lang_code', g.lang_code)
    else:
        values.setdefault('lang_code', 'en')
        g.lang_code = 'en'

@bp.url_value_preprocessor
def pull_lang_code(endpoint, values):
    g.lang_code_set = 'lang_code' in values
    g.lang_code = values.pop('lang_code', app.config['BABEL_DEFAULT_LOCALE'])
    if g.lang_code not in app.config['SUPPORTED_LANGUAGES']:
        abort(404)

@babel.localeselector
def get_locale():
    return g.lang_code

@bp.route('/', methods=['GET'])
def page_home():
    return render_template('home.html')

@bp.route('/fulltext/search', methods=['GET', 'POST'])
def fulltext_search():

    query = request.args.get('q')
    filter_type = request.args.get('filter_type') or 'papers'
    filter_time = request.args.get('filter_time') or 'all_time'

    offset = request.args.get('offset', '0')
    offset = max(0, int(offset)) if offset.isnumeric() else 0

    if 'q' in request.args.keys():
        found = do_fulltext_search(query, offset=offset, filter_type=filter_type, filter_time=filter_time)
        return render_template('fulltext_search.html', found=found, query=query, filter_type=filter_type, filter_time=filter_time)
    else:
        return render_template('fulltext_search.html', query=query, filter_type=filter_type, filter_time=filter_time)

@bp.route('/about', methods=['GET'])
def page_about():
    return render_template('about_{}.html'.format(g.lang_code))

@bp.route('/sources', methods=['GET'])
def page_sources():
    return render_template('sources_{}.html'.format(g.lang_code))

# TODO: how to translate these pages? lang_code issue
#@bp.app_errorhandler(404)
#def page_not_found(e):
#    return render_template('404.html'), 404

#@bp.app_errorhandler(502)
#@bp.app_errorhandler(503)
#@bp.app_errorhandler(504)
#@bp.app_errorhandler(500)
#def page_server_error(e):
#    return render_template('500.html'), 500

@bp.app_errorhandler(400)
def page_bad_request(e):
    return render_template('400.html'), 400

@app.route('/robots.txt', methods=['GET'])
def robots():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'robots.txt',
                               mimetype='text/plain')

app.register_blueprint(bp, url_prefix='/<string(length=2):lang_code>/')
app.register_blueprint(bp, url_prefix='/')
