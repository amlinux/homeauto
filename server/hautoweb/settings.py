# Django settings for hautoweb project.

import os
import re
path = os.path.abspath(re.sub(r'\/[^\/]+$', '', __file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
ADMINS = (
    ('Alexander Lourier', 'aml@rulezz.ru'),
)
MANAGERS = ADMINS
TIME_ZONE = None
LANGUAGE_CODE = 'ru-ru'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
MEDIA_ROOT = ''
MEDIA_URL = ''
ADMIN_MEDIA_PREFIX = '/media/'
SECRET_KEY = '0q^kdo+n3w!18(k4vc%)-g373oc!ak43-d08#w*2o+lu#^0gf2'
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
#    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'hautoweb.urls'

TEMPLATE_DIRS = [
    path + "/templates"
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "hauto",
        "OPTIONS": {
            "read_default_file": path + "/../my.cnf",
            "init_command": "SET storage_engine=INNODB"
        }
    }
}

INSTALLED_APPS = (
    "hautoweb.portal",
    "hautoweb.mlansetup",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.auth",
    "staticfiles",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "staticfiles.context_processors.static_url",
    "django.contrib.auth.context_processors.auth",
    "hautoweb.portal.context_processors.menu",
)

STATICFILES_DIRS = [
    path + "/staticfiles"
]

LOGIN_URL = "/homeauto/login/"
LOGIN_REDIRECT_URL = "/"
STATIC_URL = "/st/"
