from django.conf.urls import patterns, include, url
from Basic.views import *
from django.contrib.auth import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Basic.views.home', name='home'),
    # url(r'^Basic/', include('Basic.foo.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    (r'^$', 'django.contrib.auth.views.login' ),
    ('^hello/$', hello),
    ('^now/$', now),
    ('^register/$', createUser),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', logout_view),
    ('^accounts/profile/$', profile),
    ('^thanks/$', thanks),
    ('^accounts/update/$', update),
)
