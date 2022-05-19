from .default import *
import rollbar


DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '188.225.44.163', '92.53.127.251']
INTERNAL_IPS = ['127.0.0.1', 'localhost', '188.225.44.163', '92.53.127.251']

INSTALLED_APPS += [
    'debug_toolbar',
    'django_extensions',
    'schema_graph',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'apps.users.auth.authentication.TokenAuthentication',
    'rest_framework.authentication.SessionAuthentication',
)

CORS_ALLOWED_ORIGINS += [
    'http://localhost:8080',
    'http://localhost:8081',
    'http://localhost:3000',
]

SPAGHETTI_SAUCE = {
    'apps': ['users', 'banks', 'contract', 'misc', 'orders', 'partners', 'telegram'],
    'show_fields': True,
}

RUNSERVER_PLUS_PRINT_SQL_TRUNCATE = None
SHELL_PLUS_PRINT_SQL_TRUNCATE = None


# ROLLBAR = {
#     'access_token': '9f51b0a6fa8d478b8a85d7bc8d29d651',
#     'environment': 'development',
#     'root': BASE_DIR,
# }
#
# rollbar.init(**ROLLBAR)
