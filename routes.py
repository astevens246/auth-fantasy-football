from flask import render_template, redirect, url_for, flash, request
import os
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Team, Player
from forms import LoginForm, SignupForm, TeamForm


# ========== AUTHENTICATION ROUTES ==========


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("teams_index"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("teams_index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("teams_index"))
        flash("Invalid username or password", "danger")
    return render_template("login.html", form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("teams_index"))

    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Account created!", "success")
        return redirect(url_for("teams_index"))
    return render_template("signup.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ========== TEAM ROUTES (CRUD) ==========


@app.route("/teams")
@login_required
def teams_index():
    from datetime import date

    season_start = date(2025, 9, 1)

    # Get active team (most recent team created after season start)
    active_team = (
        Team.query.filter_by(user_id=current_user.id)
        .filter(Team.created_at >= season_start)
        .order_by(Team.created_at.desc())
        .first()
    )

    # Get past teams (created before season start)
    past_teams = (
        Team.query.filter_by(user_id=current_user.id)
        .filter(Team.created_at < season_start)
        .order_by(Team.created_at.desc())
        .all()
    )

    all_teams = Team.query.all()
    return render_template(
        "teams/index.html",
        active_team=active_team,
        past_teams=past_teams,
        all_teams=all_teams,
    )


@app.route("/teams/new", methods=["GET", "POST"])
@login_required
def teams_new():
    from datetime import date

    season_start = date(2025, 9, 1)

    form = TeamForm()
    if form.validate_on_submit():
        # Check if user already has an active team
        existing_active = (
            Team.query.filter_by(user_id=current_user.id)
            .filter(Team.created_at >= season_start)
            .first()
        )
        if existing_active:
            flash("You already have an active team for this season!", "warning")
            return redirect(url_for("teams_show", id=existing_active.id))

        # Create new team
        team = Team(name=form.name.data, user_id=current_user.id)
        db.session.add(team)
        db.session.commit()
        flash("Team created!", "success")
        return redirect(url_for("teams_show", id=team.id))
    return render_template("teams/new.html", form=form)


@app.route("/teams/<int:id>")
@login_required
def teams_show(id):
    team = Team.query.get_or_404(id)
    is_owner = team.user_id == current_user.id
    can_edit = (
        is_owner and team.is_active()
    )  # Can only edit if owner and team is active

    # Get players on this team, organized by position
    all_players = Player.query.filter_by(team_id=team.id).all()
    players_qb = [p for p in all_players if p.position == "QB"]
    players_rb = [p for p in all_players if p.position == "RB"]
    players_wr = [p for p in all_players if p.position == "WR"]
    players_te = [p for p in all_players if p.position == "TE"]

    # Roster limits for display
    MAX_TOTAL_PLAYERS = 8
    MAX_PER_POSITION = {"QB": 2, "RB": 3, "WR": 3, "TE": 2}

    # Calculate roster stats
    total_players = len(all_players)
    roster_stats = {
        "total": total_players,
        "max_total": MAX_TOTAL_PLAYERS,
        "qb": len(players_qb),
        "max_qb": MAX_PER_POSITION["QB"],
        "rb": len(players_rb),
        "max_rb": MAX_PER_POSITION["RB"],
        "wr": len(players_wr),
        "max_wr": MAX_PER_POSITION["WR"],
        "te": len(players_te),
        "max_te": MAX_PER_POSITION["TE"],
    }

    return render_template(
        "teams/show.html",
        team=team,
        is_owner=is_owner,
        can_edit=can_edit,
        players_qb=players_qb,
        players_rb=players_rb,
        players_wr=players_wr,
        players_te=players_te,
        roster_stats=roster_stats,
    )


@app.route("/teams/<int:id>/edit", methods=["GET", "POST"])
@login_required
def teams_edit(id):
    team = Team.query.get_or_404(id)
    # Authorization: only team owner can edit, and only if team is active
    if team.user_id != current_user.id:
        flash("You can only edit your own team!", "danger")
        return redirect(url_for("teams_index"))
    if not team.is_active():
        flash("This team is too old to edit!", "warning")
        return redirect(url_for("teams_show", id=team.id))

    form = TeamForm()
    if form.validate_on_submit():
        team.name = form.name.data
        db.session.commit()
        flash("Team updated!", "success")
        return redirect(url_for("teams_show", id=team.id))
    elif request.method == "GET":
        form.name.data = team.name
    return render_template("teams/edit.html", form=form, team=team)


@app.route("/teams/<int:id>/delete", methods=["POST"])
@login_required
def teams_delete(id):
    team = Team.query.get_or_404(id)
    # Authorization: only team owner can delete
    if team.user_id != current_user.id:
        flash("You can only delete your own team!", "danger")
        return redirect(url_for("teams_index"))

    # Remove players from team (set team_id to None)
    Player.query.filter_by(team_id=team.id).update({Player.team_id: None})
    db.session.delete(team)
    db.session.commit()
    flash("Team deleted!", "success")
    return redirect(url_for("teams_index"))


# ========== PLAYER ROUTES ==========


@app.route("/players")
@login_required
def players_browse():
    # Import from CSV if file exists (skip duplicates)
    csv_filename = "Fantasy_Football_2025_Draft.csv"
    if os.path.exists(csv_filename):
        import csv

        count = 0
        skipped = 0
        with open(csv_filename, "r", encoding="utf-8") as file:
            # Skip first line (title), then read headers
            next(file)  # Skip title line
            reader = csv.DictReader(file)
            for row in reader:
                name = row["PLAYER NAME"].strip()
                pos_full = row["POS"].strip()
                nfl_team = row["TEAM"].strip()
                rank_str = row["RK"].strip()
                position = "".join([c for c in pos_full if c.isalpha()]).upper()
                if position in ["QB", "RB", "WR", "TE"]:
                    # Parse rank (handle empty strings)
                    try:
                        rank = int(rank_str) if rank_str else None
                    except ValueError:
                        rank = None

                    # Check if player already exists
                    existing = Player.query.filter_by(
                        name=name, position=position, nfl_team=nfl_team
                    ).first()
                    if not existing:
                        player = Player(
                            name=name,
                            position=position,
                            nfl_team=nfl_team,
                            rank=rank,
                            fantasy_points=None,
                            team_id=None,
                        )
                        db.session.add(player)
                        count += 1
                    else:
                        # Update rank from CSV if provided (always use latest CSV data)
                        if rank is not None:
                            existing.rank = rank
                        skipped += 1
        db.session.commit()
        if count > 0:
            flash(f"Imported {count} new players from CSV!", "success")

    # Query: get all players where team_id is None, organized by position and ranked
    # Players are unique across ALL teams - if team_id is set, they're unavailable
    players_qb = (
        Player.query.filter_by(team_id=None, position="QB")
        .order_by(Player.rank, Player.name)
        .all()
    )
    players_rb = (
        Player.query.filter_by(team_id=None, position="RB")
        .order_by(Player.rank, Player.name)
        .all()
    )
    players_wr = (
        Player.query.filter_by(team_id=None, position="WR")
        .order_by(Player.rank, Player.name)
        .all()
    )
    players_te = (
        Player.query.filter_by(team_id=None, position="TE")
        .order_by(Player.rank, Player.name)
        .all()
    )

    # Get user's active team only (date-based)
    from datetime import date

    season_start = date(2025, 9, 1)
    active_team = (
        Team.query.filter_by(user_id=current_user.id)
        .filter(Team.created_at >= season_start)
        .order_by(Team.created_at.desc())
        .first()
    )

    return render_template(
        "players/browse.html",
        players_qb=players_qb,
        players_rb=players_rb,
        players_wr=players_wr,
        players_te=players_te,
        active_team=active_team,
    )


@app.route("/teams/<int:team_id>/players/<int:player_id>/add", methods=["POST"])
@login_required
def players_add_to_team(team_id, player_id):
    team = Team.query.get_or_404(team_id)
    # Authorization: only team owner can add players, and only if team is active
    if team.user_id != current_user.id:
        flash("You can only add players to your own team!", "danger")
        return redirect(url_for("teams_index"))
    if not team.is_active():
        flash("This team is too old to edit!", "warning")
        return redirect(url_for("teams_index"))

    player = Player.query.get_or_404(player_id)

    # Validation: ensure player is available (not already on a team)
    if player.team_id is not None:
        flash(f"{player.name} is already on a team!", "danger")
        return redirect(url_for("players_browse"))

    # Roster limits
    MAX_TOTAL_PLAYERS = 8
    MAX_PER_POSITION = {"QB": 2, "RB": 3, "WR": 3, "TE": 2}

    # Get current roster
    current_players = Player.query.filter_by(team_id=team_id).all()
    current_count = len(current_players)

    # Check total player limit
    if current_count >= MAX_TOTAL_PLAYERS:
        flash(
            f"Team roster is full! Maximum {MAX_TOTAL_PLAYERS} players allowed.",
            "danger",
        )
        return redirect(url_for("players_browse"))

    # Check position limit
    position_count = sum(1 for p in current_players if p.position == player.position)
    if position_count >= MAX_PER_POSITION.get(player.position, 99):
        flash(
            f"Maximum {MAX_PER_POSITION.get(player.position)} {player.position}s allowed per team!",
            "danger",
        )
        return redirect(url_for("players_browse"))

    # Add player to team (players are unique across ALL teams)
    player.team_id = team_id
    db.session.commit()
    flash(f"{player.name} added to {team.name}!", "success")
    return redirect(url_for("players_browse"))


@app.route("/teams/<int:team_id>/players/<int:player_id>/remove", methods=["POST"])
@login_required
def players_remove_from_team(team_id, player_id):
    team = Team.query.get_or_404(team_id)
    if team.user_id != current_user.id:
        flash("You can only remove players from your own team!", "danger")
        return redirect(url_for("teams_index"))
    if not team.is_active():
        flash("This team is too old to edit!", "warning")
        return redirect(url_for("teams_show", id=team_id))

    player = Player.query.get_or_404(player_id)
    # Verify player is on this team
    if player.team_id != team_id:
        flash("This player is not on this team!", "danger")
        return redirect(url_for("teams_show", id=team_id))

    # Remove player from team
    player.team_id = None
    db.session.commit()
    flash(f"{player.name} removed from {team.name}!", "success")
    return redirect(url_for("teams_show", id=team_id))
