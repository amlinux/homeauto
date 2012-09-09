# Django settings for hautoweb project.

from hwserver.config import *
import os
import re
path = os.path.abspath(re.sub(r'\/[^\/]+$', '', __file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

adminName = conf("web", "adminName")
adminEmail = conf("web", "adminEmail")
if adminName and adminEmail:
    ADMINS = (
        (adminName, adminEmail),
    )
else:
    ADMINS = ()
MANAGERS = ADMINS
TIME_ZONE = None
LANGUAGE_CODE = conf("web", "language", 'en-us')
SITE_ID = 1
USE_I18N = True
USE_L10N = True
MEDIA_ROOT = ''
MEDIA_URL = ''
ADMIN_MEDIA_PREFIX = '/media/'
SECRET_KEY = conf("web", "secretKey", 'nosecretkey')
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
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'hautoweb.urls'

TEMPLATE_DIRS = [
    path + "/templates"
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": conf("database", "web", path + '/homeauto.db')
    }
}

INSTALLED_APPS = (
    "hautoweb.portal",
    "hautoweb.hwdebug",
    "hautoweb.mlansetup",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.auth",
    "django.contrib.messages",
    "django.contrib.admin",
    "staticfiles",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "staticfiles.context_processors.static_url",
    "django.contrib.auth.context_processors.auth",
    "hautoweb.portal.context_processors.menu",
    "django.contrib.messages.context_processors.messages",
)

STATICFILES_DIRS = [
    path + "/staticfiles"
]

LOGIN_URL = "/homeauto/login/"
LOGIN_REDIRECT_URL = "/"
STATIC_URL = "/st/"
