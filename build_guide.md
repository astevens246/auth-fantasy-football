# Fantasy Football Team Manager - Build Guide

## Project Overview

A Python web app (Flask or Django) where users can:

- Sign up and log in
- Create and manage their fantasy team
- Browse and add NFL players to their team
- View their team roster

---

## Step 1: Choose Framework & Setup

### Option A: Flask (Recommended for beginners)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Flask
pip install flask flask-sqlalchemy flask-login flask-bcrypt

# Create project structure
mkdir fantasy_football
cd fantasy_football
touch app.py models.py forms.py routes.py
mkdir templates static
```

### Option B: Django

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Django
pip install django

# Create project
django-admin startproject fantasy_football
cd fantasy_football
python manage.py startapp teams
python manage.py startapp accounts
```

**For this guide, we'll use Flask (simpler for this project).**

---

## Step 2: Set Up Database & Models

### 2.1 Create `app.py` (Flask app setup)

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fantasy_football.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from models import User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from routes import *
```

### 2.2 Create `models.py` (Database models)

```python
from app import db, bcrypt
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One-to-many relationship with Team
    teams = db.relationship('Team', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One-to-many relationship with Player
    players = db.relationship('Player', backref='team', lazy=True)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(10), nullable=False)  # QB, RB, WR, TE
    nfl_team = db.Column(db.String(10), nullable=False)
    fantasy_points = db.Column(db.Integer, nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)  # NULL = available
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2.3 Initialize Database

```python
# Create init_db.py
from app import app, db
from models import User, Team, Player

with app.app_context():
    db.create_all()
    print("Database created!")
```

Run: `python init_db.py`

---

## Step 3: Create Forms

### 3.1 Create `forms.py`

```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already exists.')

class TeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired(), Length(min=3, max=100)])
    submit = SubmitField('Create Team')
```

---

## Step 4: Create Routes (11 routes)

### 4.1 Create `routes.py`

```python
from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Team, Player
from forms import LoginForm, SignupForm, TeamForm

# ========== AUTHENTICATION ROUTES (4 routes) ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('teams_index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('teams_index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('teams_index'))

    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created!', 'success')
        return redirect(url_for('teams_index'))
    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ========== TEAMS RESOURCEFUL ROUTES (7 routes) ==========

@app.route('/teams')
@login_required
def teams_index():
    # Show all of user's teams
    teams = Team.query.filter_by(user_id=current_user.id).all()
    return render_template('teams/index.html', teams=teams)

@app.route('/teams/new', methods=['GET', 'POST'])
@login_required
def teams_new():
    form = TeamForm()
    if form.validate_on_submit():
        team = Team(name=form.name.data, user_id=current_user.id)
        db.session.add(team)
        db.session.commit()
        flash('Team created!', 'success')
        return redirect(url_for('teams_show', id=team.id))
    return render_template('teams/new.html', form=form)

@app.route('/teams/<int:id>')
@login_required
def teams_show(id):
    team = Team.query.get_or_404(id)
    # Authorization: only team owner can view
    if team.user_id != current_user.id:
        flash('You can only view your own team!', 'danger')
        return redirect(url_for('teams_index'))

    # Get players on this team
    players = Player.query.filter_by(team_id=team.id).all()
    return render_template('teams/show.html', team=team, players=players)

@app.route('/teams/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def teams_edit(id):
    team = Team.query.get_or_404(id)
    # Authorization: only team owner can edit
    if team.user_id != current_user.id:
        flash('You can only edit your own team!', 'danger')
        return redirect(url_for('teams_index'))

    form = TeamForm()
    if form.validate_on_submit():
        team.name = form.name.data
        db.session.commit()
        flash('Team updated!', 'success')
        return redirect(url_for('teams_show', id=team.id))
    elif request.method == 'GET':
        form.name.data = team.name
    return render_template('teams/edit.html', form=form, team=team)

@app.route('/teams/<int:id>', methods=['DELETE'])
@app.route('/teams/<int:id>/delete', methods=['POST'])
@login_required
def teams_delete(id):
    team = Team.query.get_or_404(id)
    # Authorization: only team owner can delete
    if team.user_id != current_user.id:
        flash('You can only delete your own team!', 'danger')
        return redirect(url_for('teams_index'))

    # Remove players from team (set team_id to None)
    Player.query.filter_by(team_id=team.id).update({Player.team_id: None})
    db.session.delete(team)
    db.session.commit()
    flash('Team deleted!', 'success')
    return redirect(url_for('teams_index'))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('teams_index'))
    return redirect(url_for('login'))
```

---

## Step 5: Create Templates

### 5.1 Base Template: `templates/base.html`

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Fantasy Football Manager</title>
    <link
      rel="stylesheet"
      href="{{ url_for('static', filename='style.css') }}"
    />
  </head>
  <body>
    <nav>
      {% if current_user.is_authenticated %}
      <a href="{{ url_for('teams_index') }}">My Teams</a>
      <a href="{{ url_for('logout') }}">Logout</a>
      {% else %}
      <a href="{{ url_for('login') }}">Login</a>
      <a href="{{ url_for('signup') }}">Sign Up</a>
      {% endif %}
    </nav>

    {% with messages = get_flashed_messages(with_categories=true) %} {% if
    messages %} {% for category, message in messages %}
    <div class="alert alert-{{ category }}">{{ message }}</div>
    {% endfor %} {% endif %} {% endwith %} {% block content %}{% endblock %}
  </body>
</html>
```

### 5.2 Login: `templates/login.html`

```html
{% extends "base.html" %} {% block content %}
<h1>Login</h1>
<form method="POST">
  {{ form.hidden_tag() }} {{ form.username.label }} {{ form.username() }} {{
  form.password.label }} {{ form.password() }} {{ form.submit() }}
</form>
<p>Don't have an account? <a href="{{ url_for('signup') }}">Sign up</a></p>
{% endblock %}
```

### 5.3 Signup: `templates/signup.html`

```html
{% extends "base.html" %} {% block content %}
<h1>Sign Up</h1>
<form method="POST">
  {{ form.hidden_tag() }} {{ form.username.label }} {{ form.username() }} {{
  form.email.label }} {{ form.email() }} {{ form.password.label }} {{
  form.password() }} {{ form.confirm_password.label }} {{
  form.confirm_password() }} {{ form.submit() }}
</form>
<p>Already have an account? <a href="{{ url_for('login') }}">Login</a></p>
{% endblock %}
```

### 5.4 Team Index: `templates/teams/index.html`

```html
{% extends "base.html" %} {% block content %}
<h1>My Teams</h1>
<a href="{{ url_for('teams_new') }}">Create New Team</a>

{% if teams %}
<ul>
  {% for team in teams %}
  <li>
    <a href="{{ url_for('teams_show', id=team.id) }}">{{ team.name }}</a>
    <span>Created: {{ team.created_at.strftime('%Y-%m-%d') }}</span>
  </li>
  {% endfor %}
</ul>
{% else %}
<p>
  You don't have any teams yet.
  <a href="{{ url_for('teams_new') }}">Create your first team!</a>
</p>
{% endif %} {% endblock %}
```

### 5.5 Team Show: `templates/teams/show.html`

```html
{% extends "base.html" %} {% block content %}
<h1>{{ team.name }}</h1>
<p>Created: {{ team.created_at.strftime('%Y-%m-%d') }}</p>

<h2>Players</h2>
{% if players %}
<ul>
  {% for player in players %}
  <li>{{ player.name }} - {{ player.position }} - {{ player.nfl_team }}</li>
  {% endfor %}
</ul>
{% else %}
<p>No players on your team yet.</p>
{% endif %}

<a href="{{ url_for('teams_edit', id=team.id) }}">Edit Team</a>
<form
  method="POST"
  action="{{ url_for('teams_delete', id=team.id) }}"
  style="display:inline;"
>
  <button type="submit" onclick="return confirm('Delete team?')">
    Delete Team
  </button>
</form>
<a href="{{ url_for('teams_index') }}">Back to My Teams</a>
{% endblock %}
```

### 5.6 Team New: `templates/teams/new.html`

```html
{% extends "base.html" %} {% block content %}
<h1>Create Team</h1>
<form method="POST">
  {{ form.hidden_tag() }} {{ form.name.label }} {{ form.name() }} {{
  form.submit() }}
</form>
{% endblock %}
```

### 5.7 Team Edit: `templates/teams/edit.html`

```html
{% extends "base.html" %} {% block content %}
<h1>Edit Team</h1>
<form method="POST">
  {{ form.hidden_tag() }} {{ form.name.label }} {{ form.name() }} {{
  form.submit() }}
</form>
<a href="{{ url_for('teams_show', id=team.id) }}">Cancel</a>
<a href="{{ url_for('teams_index') }}">Back to My Teams</a>
{% endblock %}
```

---

## Step 6: Seed Players from CSV

### 6.1 Create `seed_players.py`

```python
from app import app, db
from models import Player
import csv

def seed_players():
    with app.app_context():
        with open('FantasyPros_2025_Draft_ALL_Rankings.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                name = row['PLAYER NAME'].strip()
                pos_full = row['POS'].strip()
                position = ''.join([c for c in pos_full if c.isalpha()]).upper()
                nfl_team = row['TEAM'].strip()

                if position not in ['QB', 'RB', 'WR', 'TE']:
                    continue

                # Check if player already exists
                existing = Player.query.filter_by(name=name, position=position).first()
                if existing:
                    continue

                player = Player(
                    name=name,
                    position=position,
                    nfl_team=nfl_team,
                    fantasy_points=None,
                    team_id=None
                )
                db.session.add(player)

        db.session.commit()
        print("Players seeded!")

if __name__ == '__main__':
    seed_players()
```

Run: `python seed_players.py`

---

## Step 7: Create Tests

### 7.1 Create `tests.py`

```python
import unittest
from app import app, db
from models import User, Team, Player

class TestRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.app = app.test_client()
        db.create_all()

        # Create test user
        user = User(username='testuser', email='test@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_login_success(self):
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_login_failure(self):
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertIn(b'Invalid', response.data)

    def test_signup(self):
        response = self.app.post('/signup', data={
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_team_creation(self):
        # Login first
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        response = self.app.post('/teams/new', data={
            'name': 'Test Team'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_team_authorization(self):
        # Create another user
        user2 = User(username='user2', email='user2@test.com')
        user2.set_password('password123')
        db.session.add(user2)

        # Create team for user2
        team = Team(name='User2 Team', user_id=2)
        db.session.add(team)
        db.session.commit()

        # Login as testuser
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })

        # Try to edit user2's team
        response = self.app.get(f'/teams/{team.id}/edit', follow_redirects=True)
        self.assertIn(b'own team', response.data)

    def test_protected_route(self):
        response = self.app.get('/teams/new', follow_redirects=True)
        self.assertIn(b'Login', response.data)

if __name__ == '__main__':
    unittest.main()
```

Run: `python tests.py`

---

## Step 8: Run the App

```bash
# Set Flask app
export FLASK_APP=app.py
export FLASK_ENV=development

# Run
flask run
```

Visit: `http://localhost:5000`

---

## Checklist

- [ ] Flask app setup
- [ ] Database models (User, Team, Player)
- [ ] Forms (Login, Signup, Team)
- [ ] 11 routes (4 auth + 7 resourceful)
- [ ] Templates (base, login, signup, teams index, teams show, teams new, teams edit)
- [ ] Seed players from CSV
- [ ] Authorization (users can only edit own team)
- [ ] Tests (6+ route tests)
- [ ] Run and test the app

---

## Next Steps (Optional)

- Add player browsing page
- Add "Add Player to Team" functionality
- Add "Remove Player from Team" functionality
- Improve styling with CSS
- Add player statistics

Good luck! 🏈
