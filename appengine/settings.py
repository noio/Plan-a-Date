"""Minimal Django settings."""

import os

APPEND_SLASH = True
DEBUG = True
INSTALLED_APPS = ('planadate',)
ROOT_PATH = os.path.dirname(__file__)
ROOT_URLCONF = 'urls'
MIDDLEWARE_CLASSES = (
    #'google.appengine.ext.appstats.recording.AppStatsDjangoMiddleware',
    #'firepython.middleware.FirePythonDjango',
    #'appstats.recording.AppStatsDjangoMiddleware',
    'django.middleware.common.CommonMiddleware',
	'planadate.middleware.AddUserToRequestMiddleware'
    #'django.middleware.http.ConditionalGetMiddleware',
)
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
)
TEMPLATE_STRING_IF_INVALID = 'err{{%s}}' if DEBUG else ''
TEMPLATE_DEBUG = DEBUG
TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'templates'),
)
MEDIA_URL = '/static/'

