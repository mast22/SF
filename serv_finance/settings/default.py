from pathlib import Path
import environ, os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(env_file=os.path.join(BASE_DIR, '.env'))

SECRET_KEY = 'hjzw%dw&wxg=-9^3#o)0boo$34$k@8=#t=jg@%p=i-$8p#0#oo'

INSTALLED_APPS = [
    'channels',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.auth',
    'phonenumber_field',
    'rest_framework',
    'django_filters',
    'drf_yasg',
    'corsheaders',
    'django_dramatiq',
    'django_apscheduler',
    'apps.misc',
    'apps.users',
    'apps.partners',
    'apps.orders',
    'apps.banks',
    'apps.testing',
    'apps.deliveries',
    'apps.telegram',
    'apps.msgs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Убрать и заменит CommonMiddleware когда запросим установку нового адреса у ОТП
    # 'apps.common.middleware.OTPAppendSlashWorkAroundCommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'serv_finance.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'serv_finance.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL'),
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

AUTHENTICATION_BACKENDS = (
    # 'apps.users.auth.authentication.ModelBackend',
    'django.contrib.auth.backends.ModelBackend',
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('TIME_ZONE', str, default='Europe/Moscow')
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = env('STATIC_ROOT', str, default=os.path.join(BASE_DIR, 'STATIC'))
MEDIA_ROOT = env('BASE_DIR', str, default=os.path.join(BASE_DIR, 'MEDIA'))
MEDIA_URL = '/media/'

REST_FRAMEWORK = {
    # 'DEFAULT_PERMISSION_CLASSES': ('apps.common.permissions.permissions.DefaultAccessPolicy',),
    'DATETIME_FORMAT': 'iso-8601',
    # 'DATETIME_INPUT_FORMATS': ('%s', 'iso-8601',) if REST_DATETIME_UNIX_TIMESTAMP else ('iso-8601',),
    'DEFAULT_FILTER_BACKENDS': (
        # 'rest_framework_json_api.filters.QueryParameterValidationFilter',
        # 'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework_json_api.filters.OrderingFilter',
        'rest_framework_json_api.django_filters.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    ),
    'SEARCH_PARAM': 'filter[search]',
    'DEFAULT_RENDERER_CLASSES': [
        # 'rest_framework_json_api.renderers.JSONRenderer',
        'rest_framework.renderers.JSONRenderer',
        'drf_renderer_xlsx.renderers.XLSXRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'apps.common.renderers.BrowsableAPIRendererWithoutForms',
        'apps.common.renderers.BrowsableAPIRendererWithoutPostForm',
        'rest_framework.renderers.AdminRenderer',
        # 'rest_framework.renderers.SchemaJSRenderer',
        # 'rest_framework.renderers.DocumentationRenderer',
        # 'rest_framework.renderers.HTMLFormRenderer',
        # 'rest_framework.renderers.CoreAPIOpenAPIRenderer',
        # 'rest_framework.renderers.CoreAPIJSONOpenAPIRenderer',
        # 'rest_framework.renderers.OpenAPIRenderer',
        # 'rest_framework.renderers.JSONOpenAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),
    # 'EXCEPTION_HANDLER': 'apps.common.exceptions.exception_handler.custom_exception_handler',
    'EXCEPTION_HANDLER': 'rest_framework_json_api.exceptions.exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.PageNumberPagination',
    'PAGE_SIZE': env('REST_FRAMEWORK_PAGE_SIZE', int, default=10),
    'TEST_REQUEST_RENDERER_CLASSES': (
        'rest_framework_json_api.renderers.JSONRenderer',
        'rest_framework.renderers.JSONRenderer',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'vnd.api+json',
    'COERCE_DECIMAL_TO_STRING': False,
}

PERMISSIONS_SETTINGS = {
    'reusable_conditions': 'apps.common.permissions.reusable_conditions',
    'print_log': env('PERMISSIONS_SETTINGS_PRINT_LOG', bool, False),
}

SWAGGER_SETTINGS = {
    'DEFAULT_AUTO_SCHEMA_CLASS': 'drf_yasg_json_api.inspectors.SwaggerAutoSchema',  # Overridden

    'DEFAULT_FIELD_INSPECTORS': [
        'drf_yasg_json_api.inspectors.NamesFormatFilter',  # Replaces CamelCaseJSONFilter
        'drf_yasg.inspectors.RecursiveFieldInspector',
        'drf_yasg_json_api.inspectors.XPropertiesFilter',  # Added
        'drf_yasg_json_api.inspectors.JSONAPISerializerSmartInspector',  # Added
        'drf_yasg.inspectors.ReferencingSerializerInspector',
        'drf_yasg_json_api.inspectors.IntegerIDFieldInspector',  # Added
        'drf_yasg.inspectors.ChoiceFieldInspector',
        'drf_yasg.inspectors.FileFieldInspector',
        'drf_yasg.inspectors.DictFieldInspector',
        'drf_yasg.inspectors.JSONFieldInspector',
        'drf_yasg.inspectors.HiddenFieldInspector',
        'drf_yasg_json_api.inspectors.ManyRelatedFieldInspector',  # Added
        'drf_yasg_json_api.inspectors.IntegerPrimaryKeyRelatedFieldInspector',  # Added
        'drf_yasg.inspectors.RelatedFieldInspector',
        'drf_yasg.inspectors.SerializerMethodFieldInspector',
        'drf_yasg.inspectors.SimpleFieldInspector',
        'drf_yasg.inspectors.StringDefaultFieldInspector',

    ],
    'DEFAULT_FILTER_INSPECTORS': [
        'drf_yasg_json_api.inspectors.DjangoFilterInspector',  # Added (optional), requires django_filter
        'drf_yasg.inspectors.CoreAPICompatInspector',
    ],
    'DEFAULT_PAGINATOR_INSPECTORS': [
        'drf_yasg_json_api.inspectors.DjangoRestResponsePagination',  # Added
        'drf_yasg.inspectors.DjangoRestResponsePagination',
        'drf_yasg.inspectors.CoreAPICompatInspector',
    ],
    # 'DEFAULT_API_URL': 'schema-json',
    'SPEC_URL': 'api:schema-json',
    'DEFAULT_INFO': 'apps.api.schema.api_info'
}

REDOC_SETTINGS = {
    'LAZY_RENDERING': True,
    'SPEC_URL': 'api:schema-json',
}

SHELL_PLUS_IMPORTS = [
    'from apps.users.const import *',
    'from apps.orders.const import *',
    'from apps.partners.const import *',
]

DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.redis.RedisBroker",
    "OPTIONS": {
        "url": "redis://localhost:6379",
    },
    "MIDDLEWARE": [
        "apps.misc.dramatiq_broker.RollbarMiddleware",
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ]
}

# Для использования в тестах
DRAMATIQ_TEST_BROKER = {
    "BROKER": "dramatiq.brokers.stub.StubBroker",
    "OPTIONS": {},
    "MIDDLEWARE": [
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Pipelines",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ]
}

TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN', str, default='')

AUTH_SETTINGS = {
    'ENABLE_IP_LIMITATION': env('ENABLE_IP_LIMITATION', bool, default=True),
}

USE_REDIS = True

# Определения провайдеров и их настройки.
MESSAGES_PROVIDERS = {
    'smsc.ru': {
        'provider': 'apps.msgs.providers.smsc.SmscProvider',
        'provider_settings': {
            'login': env('MESSAGES_PROVIDER_SMSCRU_LOGIN', str, default=''),
            'password': env('MESSAGES_PROVIDER_SMSCRU_PASSWORD', str, default=''),
            'sms_from': env('MESSAGES_PROVIDER_SMSCRU_SMS_FROM', str, default='RedBox'),
        },
        'settings': {},
    },
    'smsint.ru': {
        'provider': 'apps.msgs.providers.smsint.SmsintProvider',
        'provider_settings': {
            'login': env('MESSAGES_PROVIDER_SMSINT_LOGIN', str, default=''),
            'password': env('MESSAGES_PROVIDER_SMSINT_PASSWORD', str, default=''),
            'sms_from': env('MESSAGES_PROVIDER_SMSINT_SMS_FROM', str, default='RedBox'),
        },
        'settings': {},
    },
    'unisender.com': {
        'provider': 'apps.msgs.providers.unisender.UnisenderProvider',
        'provider_settings': {
            'api_key': env('MESSAGES_PROVIDER_UNISENDERCOM_API_KEY', str, default=''),
            'login': env('MESSAGES_PROVIDER_UNISENDERCOM_LOGIN', str, default=''),
            'sms_from': env('MESSAGES_PROVIDER_UNISENDERCOM_SMS_FROM', str, default='RedBox'),
            'email_from': env('MESSAGES_PROVIDER_UNISENDERCOM_EMAIL_FROM', str, default='RedBox'),
            'email_from_name': env('MESSAGES_PROVIDER_UNISENDERCOM_EMAIL_FROM_NAME', str, default='Redbox'),
        },
        'settings': {},
    },
    # 'sendpulse.com': {
    #     'provider': 'apps.msgs.providers.smsint.SendPulseProvider',
    #     'provider_settings': {},
    #     'settings': {},
    # },
    'dummy_provider': {
        'provider': 'apps.testing.msgs_providers_dummy.DummyProvider',
        'provider_settings': {},
        'settings': {},
    },
    'telegram-client': {
        'provider': 'apps.msgs.providers.telegram.TelegramProvider',
        'provider_settings': {},
        'settings': {},
    }
}

MESSAGES_SETTINGS = {
    # 'auth-code': {
    #     'sms': {'method': 'send_auth_code', 'provider': 'smsc.ru'},
    #     'dialing': {'method': 'send_dialing', 'provider': 'smsc.ru'},
    # },
    # For tests:
    'auth-code': {
        'sms': {
            'method': 'send_auth_code',
            'provider': env('MESSAGES_AUTH_CODE_PROVIDER', str, default='dummy_provider'),
            'options': {'code_length': 4},
        },
        'dialing': {
            'method': 'send_auth_code',
            'provider': env('MESSAGES_AUTH_CODE_PROVIDER', str, default='dummy_provider'),
            'options': {'code_length': 6},
        },
    },
    'notification': {
        'push': {
            'method': 'send_push',
            'choose_provider_by': 'apps.msgs.utils.push_provider_selector',
            'providers': {
                'APNS': 'apns',
                'FCM': 'fcm',
                'WEB': 'dummy_provider',
                'DUMMY': 'dummy_provider',
            }
        },
        'email': {'method': 'send_email', 'provider': 'unisender.com'},
        'telegram': {
            'method': 'send_telegram_message',
            'provider': 'telegram-client',
        }
    }
}

# CORS settings: https://github.com/adamchainz/django-cors-headers
CORS_ALLOWED_ORIGINS = [
    'http://92.53.127.251',
    'https://92.53.127.251',
    'http://188.225.44.163',
    'https://188.225.44.163'
]

# Коды данной системы у банков для интеграции
OTP_SW_CODE = 'CRED_IT_TEST'
POCHTA_SW_CODE = 'CRED_IT_TEST'  # не установлен
MTS_SW_CODE = 'CRED_IT_TEST'  # не установлен

# Некоторые показатели, как допустим комиссия, создаются во время выполнения системы,
# Однако создания комисии зависит от наличия агента, поэтому можно попробовать не высчитывать
# её там, где можно без неё обойтись. В частности, для тестов используется
# @override_settings(CALCULATE_OPERATIONAL_DATA=False)
CALCULATE_OPERATIONAL_DATA = env('CALCULATE_OPERATIONAL_DATA', bool, default=True)

# Для отправки в банк используются заглушки, данные которые они принимают для того чтобы скоринг проходил
PLUG_MODE = env('PLUG_MODE', bool, default=True)
# Верификация SSL сертификата (точно не знаю что это), но без этого не работает. Необходимо для отправки XML
VERIFY_SSL = env('VERIFY_SSL', bool, default=False)
# Дублируем запрос на STAGE/DEV сервер. Банки делают колбеки для оповещения нас с помощью HTTP запроса
# Однако для нас PROD и STAGE оба работают как тестовые серверы для банков и указать единовременно можно только 1 сервер
# Если колбек приходит к нам, то мы его дублируем на тестовый и каждый из серверов сам принимает решение об обработке
# запроса
REDIRECT_CALLBACKS_TO_STAGE = env('REDIRECT_CALLBACKS_TO_STAGE', bool, default=False)

POCHTA_API_VERSION = 'MultistepRTDMv2'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': env('LOG_FILE', str, default=os.path.join(BASE_DIR, 'debug.log')),
            'formatter': 'standard',
        },
        'file_info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': env('LOG_INFO_FILE', str, default=os.path.join(BASE_DIR, 'logger_info.log')),
            'formatter': 'standard',
        },
        'scoring': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': env('LOG_SCORING', str, default=os.path.join(BASE_DIR, 'scoring_info.log')),
            'formatter': 'standard'
        },
        'file_testing': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': env('LOG_TESTING', str, default=os.path.join(BASE_DIR, 'testing_info.log')),
            'formatter': 'standard'
        },
        'web_socket': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': env('LOG_WEBSOCKET', str, default=os.path.join(BASE_DIR, 'websocket_info.log')),
            'formatter': 'standard',
        },
        # 'tasks': {
        #     'level': 'INFO',
        #     'class': 'logging.FileHandler',
        #     'filename': env('LOG_TASKS', str, default=os.path.join(BASE_DIR, 'tasks_info.log')),
        #     'formatter': 'standard',
        # }
    },
    'loggers': {
        'apps': {
            'level': 'DEBUG',
            'handlers': ['file_debug'],
        },
        '': {
            'level': 'INFO',
            'handlers': ['file_info'],
        },
        'testing': {
            'level': 'INFO',
            'handlers': ['file_testing']
        },
        # Логирование веб-сокетов
        'web_socket': {
            'level': 'INFO',
            'handlers': ['web_socket'],
        },
        'django.channels.server': {
            'level': 'INFO',
            'handlers': ['web_socket'],
        },
        'daphne.server': {
            'level': 'INFO',
            'handlers': ['web_socket'],
        },
        # Логирование скоринга
        'scoring': {
            'handlers': ['scoring'],
            'level': 'DEBUG',
        },
        # Логирование задач
        # 'tasks': {
        #     'handlers': ['tasks'],
        #     'level': 'INFO',
        # }
    }
}

# Channels
ASGI_APPLICATION = 'serv_finance.routing.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}

# Настройки кэша:
if USE_REDIS:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://localhost:6379/1',
            'TIMEOUT': 60 * 60 * 12,  # По умолчанию таймаут записи кэша: 12 часов.
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PARSER_CLASS': 'redis.connection.HiredisParser',
                'PASSWORD': None,
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'IGNORE_EXCEPTIONS': False,
            }
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 60 * 60 * 12,
            'OPTIONS': {
                'IGNORE_EXCEPTIONS': True,
            }
        },
    }



# MIDDLEWARE += [
#     'rollbar.contrib.django.middleware.RollbarNotifierMiddleware',
# ]
