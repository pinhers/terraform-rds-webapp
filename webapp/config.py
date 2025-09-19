import os

DB_HOST = "flask-db.cnuocu8suj74.eu-west-1.rds.amazonaws.com"
DB_NAME = "flask-db"
DB_USER = "ITadmin"
DB_PASS = "yourpassword"

SQLALCHEMY_DATABASE_URI = f"postgresql://ITadmin:yourpassword@flask-db.cnuocu8suj74.eu-west-1.rds.amazonaws.com:5432/flask-db"
SQLALCHEMY_TRACK_MODIFICATIONS = False
