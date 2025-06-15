import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trunk.settings")

application = get_wsgi_application()
app=application #some deployment issue