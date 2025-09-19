Create a `app.py` file:

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

#Define a simple model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)

@app.route('/')
def index():
    return "Flask App Connected to AWS RDS PostgreSQL!"

if __name__ == '__main__':
    app.run(debug=True)
