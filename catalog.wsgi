import sys
import random
import string
sys.path.append('/var/www/html/catalog')
from views import app as application
application.secret_key = ''.join(
                    random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
