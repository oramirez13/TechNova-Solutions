import os
import sys


PROJECT_HOME = "/home/yourusername/TechNova-Solutions/flask/technova_solutions_render"
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)


os.environ["TECHNOVA_DB_ENGINE"] = "mysql"
os.environ["TECHNOVA_DB_HOST"] = "yourusername.mysql.pythonanywhere-services.com"
os.environ["TECHNOVA_DB_USER"] = "yourusername"
os.environ["TECHNOVA_DB_PASSWORD"] = "your-mysql-password"
os.environ["TECHNOVA_DB_NAME"] = "yourusername$technova"
os.environ["SECRET_KEY"] = "replace-this-secret"


from app import app as application
