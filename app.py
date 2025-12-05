from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
database_url = os.environ.get("DATABASE_URL")

# Use PostgreSQL on Render, SQLite locally
if database_url:
    # Render provides DATABASE_URL, but SQLAlchemy needs postgresql:// not postgres://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # Local development - use SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fantasy_football.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    from models import User

    try:
        return User.query.get(int(user_id))
    except:
        return None


from routes import *

# Initialize database tables on startup
with app.app_context():
    from models import User, Team, Player

    db.create_all()
    print("Database tables initialized!")

if __name__ == "__main__":
    app.run(debug=True)
