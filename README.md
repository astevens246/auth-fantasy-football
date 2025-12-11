# Fantasy Football Manager

A full-stack web application built with Flask that allows users to create and manage fantasy football teams, browse NFL players, and build their rosters with position-based limits.

## Features

### 🔐 User Authentication

- **Sign Up**: Create an account with username, email, and password
- **Login/Logout**: Secure authentication with password hashing (bcrypt)
- **Session Management**: Persistent login sessions using Flask-Login

### 👥 Team Management

- **Create Teams**: Build your fantasy football team with a custom name
- **View Teams**: See all your teams organized by active and past seasons
- **Edit Teams**: Update team names (only for active teams)
- **Delete Teams**: Remove teams and automatically free up players
- **Season-Based System**: One active team per season (date-based activation)

### 🏈 Player Management

- **Browse Players**: View available NFL players organized by position (QB, RB, WR, TE)
- **Player Rankings**: See players sorted by fantasy rankings
- **Add Players**: Add players to your team with automatic roster validation
- **Remove Players**: Drop players from your roster
- **CSV Import**: Automatically import player data from CSV files

### 📊 Roster Management

- **Position Limits**:
  - Maximum 2 Quarterbacks (QB)
  - Maximum 3 Running Backs (RB)
  - Maximum 3 Wide Receivers (WR)
  - Maximum 2 Tight Ends (TE)
  - Maximum 10 total players per team
- **Roster Stats**: View current roster counts vs. maximum limits
- **Player Uniqueness**: Each player can only be on one team at a time

### 🔒 Security & Authorization

- **Password Security**: Passwords are hashed using bcrypt (never stored in plain text)
- **User Authorization**: Users can only edit/delete their own teams
- **Protected Routes**: Login required for team and player management
- **Active Team Restrictions**: Only active teams can be edited or modified

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (local) / PostgreSQL (production)
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login, Flask-Bcrypt
- **Forms**: Flask-WTF, WTForms
- **Migrations**: Flask-Migrate

## Database Models

### User

- Stores user account information (username, email, password hash)
- One-to-many relationship with Teams

### Team

- Represents a fantasy football team
- Belongs to a User
- Has many Players
- Tracks creation date for season-based activation

### Player

- Stores NFL player information (name, position, NFL team, rank)
- Can belong to one Team (or be a free agent)

## Routes

### Authentication (4 routes)

- `GET/POST /login` - User login
- `GET/POST /signup` - User registration
- `GET /logout` - User logout
- `GET /` - Home page (redirects based on auth status)

### Teams (5 routes)

- `GET /teams` - List all user's teams
- `GET/POST /teams/new` - Create a new team
- `GET /teams/<id>` - View team details and roster
- `GET/POST /teams/<id>/edit` - Edit team name
- `POST /teams/<id>/delete` - Delete a team

### Players (3 routes)

- `GET /players` - Browse available players
- `POST /teams/<team_id>/players/<player_id>/add` - Add player to team
- `POST /teams/<team_id>/players/<player_id>/remove` - Remove player from team

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository
2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:

   ```bash
   python init_db.py
   ```

5. (Optional) Seed players from CSV:

   ```bash
   python seed_players.py
   ```

6. Run the application:

   ```bash
   python app.py
   ```

7. Visit `http://localhost:5000` in your browser

## Testing

Run the test suite:

```bash
python tests.py
```

The test suite includes 6 route tests covering:

- Login page loading
- Successful login
- Login failure
- User signup
- Team creation
- Protected route authorization

## Key Features Explained

### Season-Based Team Activation

Teams created after September 1, 2025 are considered "active" for the current season. Only active teams can be edited or have players added/removed. This prevents modification of past season teams.

### Roster Validation

When adding players, the system automatically checks:

- Total roster size (max 10 players)
- Position-specific limits
- Player availability (not already on another team)

### CSV Player Import

The app can automatically import player data from `Fantasy_Football_2025_Draft.csv`. Players are organized by position and ranked. The import skips duplicates and updates existing player rankings.

## License

This project was created as a final project for ACS 1220.
