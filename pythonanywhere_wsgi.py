import os
import sys


PROJECT_HOME = "/home/yourusername/TechNova-Solutions/flask/technova_solutions_render"
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)


os.environ["TECHNOVA_DB_ENGINE"] = "sqlite"
os.environ["TECHNOVA_SQLITE_PATH"] = (
    "/home/yourusername/TechNova-Solutions/flask/technova_solutions_render/database/technova.sqlite3"
)
os.environ["SECRET_KEY"] = "replace-this-secret"


from app import app as application
