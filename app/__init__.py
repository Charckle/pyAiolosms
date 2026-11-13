import logging
from os import environ

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_wtf.csrf import CSRFProtect

load_dotenv()

from app.controllers.auth import current_user_view
from app.lertify import configured
from app.models import UserM
from app.roles import UserRole, role_label


def _path_matches(path: str, prefix: str) -> bool:
    normalized = path.rstrip('/') or '/'
    prefix = prefix.rstrip('/') or '/'
    return normalized == prefix or normalized.startswith(prefix + '/')


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)

    env_config = environ.get('ENVCONFIG', 'DEV').upper()
    if env_config == 'PROD':
        app.config.from_object('config.ProductionConfig')
    elif env_config == 'TEST':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.DevelopmentConfig')

    if overrides:
        app.config.update(overrides)

    csrf = CSRFProtect(app)

    from app import db
    db.init_app(app)

    logging_level = getattr(logging, app.config.get('APP_LOGGING', 'INFO'), logging.INFO)
    app.logger.setLevel(logging_level)

    @app.before_request
    def enforce_read_only_mode():
        if not app.config.get('READ_ONLY_MODE'):
            return None
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return None
        if _path_matches(request.path, '/login'):
            return None
        if request.path.startswith('/api/'):
            return jsonify(error='Instance is in read-only mode.'), 403
        flash('Instance is in read-only mode. Changes are not allowed.', 'error')
        if request.referrer:
            return redirect(request.referrer)
        return redirect(url_for('main.index'))

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith('/api/'):
            return jsonify(error='Not found.'), 404
        return render_template('404.html'), 404

    @app.route('/health')
    def health():
        return jsonify(status='healthy'), 200

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favicon.ico')

    from app.controllers.admin import admin_module
    from app.controllers.api import api_module
    from app.controllers.auth import main
    from app.controllers.sms import sms_module

    app.register_blueprint(main)
    app.register_blueprint(sms_module)
    app.register_blueprint(admin_module)
    app.register_blueprint(api_module)
    csrf.exempt(api_module)

    @app.context_processor
    def inject_globals():
        current_user = current_user_view()
        read_only_mode = bool(app.config.get('READ_ONLY_MODE'))
        can_write = (
            not read_only_mode
            and current_user is not None
            and current_user.get('role', 99) <= UserRole.READWRITE.value
        )
        return dict(
            UserRole=UserRole,
            role_label=role_label,
            current_user=current_user,
            read_only_mode=read_only_mode,
            can_write=can_write,
            can_send=can_write,
            lertify_ready=configured(),
        )

    env_label = 'production' if env_config == 'PROD' else 'development'
    with app.app_context():
        needs_admin_setup = UserM.needs_setup()
        lertify_ready = configured()
    read_only = bool(app.config.get('READ_ONLY_MODE'))

    print(f"{app.config['APP_NAME']} — SMS gateway", flush=True)
    print(f'Environment: {env_label} ({env_config})', flush=True)
    print(f'Read-only mode: {"ON" if read_only else "OFF"}', flush=True)
    if needs_admin_setup:
        print('Admin setup: REQUIRED (no users yet — open /setup/)', flush=True)
    else:
        print('Admin setup: not required (users already exist)', flush=True)
    print(f'Lertify: {"configured" if lertify_ready else "set LERTIFY_API_KEY and LERTIFY_SENDER"}', flush=True)

    app.logger.info(
        'pyAiolosms started (environment=%s, read_only=%s, admin_setup_required=%s, lertify=%s)',
        env_label, read_only, needs_admin_setup, lertify_ready,
    )
    return app
