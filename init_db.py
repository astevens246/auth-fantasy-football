from app import app, db
from models import User, Team, Player

with app.app_context():
    db.create_all()
    print("Database created with User, Team, and Player tables!")
