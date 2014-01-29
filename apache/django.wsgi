import os
import sys

path = '/home/noah/Documents/Web/Basic'
if path not in sys.path:
	sys.path.append(path)
	
os.environ['DJANGO_SETTINGS_MODULE'] = 'Basic.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
