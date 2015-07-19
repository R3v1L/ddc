# -*- coding: utf-8 -*-
###############################################################################
# Author: (C) 2012 Oliver Gutiérrez
# Module: settings
# Description: Django project settings module
###############################################################################

# Python imports
import os,sys,locale

# Debugging settings
DEBUG = TEMPLATE_DEBUG = True

# Project and applications directories
PROJECT_DIR=os.path.abspath(os.path.dirname(__name__))
APPLICATIONS_DIR=PROJECT_DIR + '/apps'

# Add current apps directory to python path
if not APPLICATIONS_DIR in sys.path:
	sys.path.insert(0,APPLICATIONS_DIR)

# Site identifier for sites application
SITE_ID = 1

# Root URLs module
ROOT_URLCONF = 'urls'

# Administrators information
ADMINS = MANAGERS = (
    ('Administrator name', 'root@localhost'),
)

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',    # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': PROJECT_DIR + '/django.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',   		                   # Set to empty string for localhost
        'PORT': '',             		   # Set to empty string for default
    }
}

# Search in apps directory for apps and load them automatically
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
]

# Conditional applications
if SITE_ID:
	INSTALLED_APPS.append('django.contrib.sites')

# Automatically add applications in apps directory
for i in os.listdir(APPLICATIONS_DIR):
	if os.path.isdir('%s/%s' % (APPLICATIONS_DIR,i)) and os.path.exists('%s/%s/__init__.py' % (APPLICATIONS_DIR,i)):
		INSTALLED_APPS.append(i)

# Get Local time zone for this installation
if os.path.exists('/etc/timezone'):
	fd=open('/etc/timezone','r')
	TIME_ZONE = fd.readline().strip()
	fd.close()
else:
	TIME_ZONE = 'Atlantic/Canary'

# Language code for this installation
LANGUAGE_CODE=locale.getdefaultlocale()[0].lower().replace('_','-')

# Internationalization settings
USE_I18N = USE_L10N = True


# Absolute path to the directory that will hold user-uploaded files
MEDIA_ROOT = PROJECT_DIR + '/media/'
# URL that handles the media served from MEDIA_ROOT
MEDIA_URL = '/media/'


# Absolute path to the directory static files should be collected to
STATIC_ROOT = PROJECT_DIR + '/static/'
# URL prefix for static files
STATIC_URL = '/static/'
# URL prefix for admin static files
ADMIN_MEDIA_PREFIX = '/static/admin/'
# Additional locations of static files
STATICFILES_DIRS = ()
# List of finder classes that know how to find static files
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.Loader'
)
# Additional locations of template files
TEMPLATE_DIRS = ()

# Middleware modules
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
)

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Unique key
SECRET_KEY = '82b!n777p&01h#8h7@%lnswma487%^d=a=tr)!g%^2^ikc9)@y'
