from .default import *
import rollbar


DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '92.53.127.251']
INTERNAL_IPS = ['127.0.0.1', 'localhost', '92.53.127.251']

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'apps.users.auth.authentication.TokenAuthentication',
)


# ROLLBAR = {
#     'access_token': '9f51b0a6fa8d478b8a85d7bc8d29d651',
#     'environment': 'production',
#     'root': BASE_DIR,
# }
#
# rollbar.init(**ROLLBAR)
