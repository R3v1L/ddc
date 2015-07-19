# -*- coding: utf-8 -*-
###############################################################################
# Author: (C) 2012 Oliver Gutiérrez
# Module: urls
# Description: Django project URLs module
###############################################################################

# Python imports
import os

# Django imports
from django.conf.urls.defaults import patterns, include, url

# Enable administration application
from django.contrib import admin
admin.autodiscover()

# Import django settings
from django.conf import settings

# Default URLs
apps_urls=['']

# Automatically add URLs for applications in apps directory
for i in os.listdir(settings.APPLICATIONS_DIR):
	appdir='%s/%s/' % (settings.APPLICATIONS_DIR,i)
	if os.path.isdir(appdir) and os.path.exists(appdir + '__init__.py') and os.path.exists(appdir + 'urls.py'):
		apps_urls.append(url(r'^' + i + '/', include(i + '.urls')))

apps_urls.extend([
    # Admin site URLs
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    # Home URL
    # url(r'^$', '', name='home'),
])

# Configure URL patterns
urlpatterns = patterns(*apps_urls)  

