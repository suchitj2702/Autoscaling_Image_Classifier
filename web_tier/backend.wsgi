#backend.wsgi
import sys
sys.path.insert(0, '/var/www/html/web_tier/')

from app import app as application
