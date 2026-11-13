from os import environ


def _flag(name, default='False'):
    return environ.get(name, default).lower() in ['true', '1', 't', 'y', 'yes']


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = environ.get('SECRET_KEY', 'change-me-before-production-use-a-random-50-char-string')

    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = _flag('WTF_CSRF_ENABLED', 'True')
    READ_ONLY_MODE = _flag('READ_ONLY_MODE', 'False')

    APP_NAME = environ.get('APP_NAME', 'pyAiolosms')
    APP_LOGGING = environ.get('APP_LOGGING', 'INFO')
    DATA_DIR = environ.get('DATA_DIR', 'data')

    LERTIFY_API_KEY = environ.get('LERTIFY_API_KEY', '')
    LERTIFY_SENDER = environ.get('LERTIFY_SENDER', '')
    LERTIFY_API_URL = environ.get('LERTIFY_API_URL', 'https://api.lertify.app/v1/sms/messages')
    DEFAULT_COUNTRY_CODE = environ.get('DEFAULT_COUNTRY_CODE', '386')


class ProductionConfig(Config):
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
