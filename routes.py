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
    teams = Team.query.filter_by(user_id=current_user.id).all()
    return render_template("teams/index.html", teams=teams)


@app.route("/teams/new", methods=["GET", "POST"])
@login_required
def teams_new():
    form = TeamForm()
    if form.validate_on_submit():
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
    # Authorization: only team owner can view
    if team.user_id != current_user.id:
        flash("You can only view your own team!", "danger")
        return redirect(url_for("teams_index"))

    # Get players on this team
    players = Player.query.filter_by(team_id=team.id).all()
    return render_template("teams/show.html", team=team, players=players)


@app.route("/teams/<int:id>/edit", methods=["GET", "POST"])
@login_required
def teams_edit(id):
    team = Team.query.get_or_404(id)
    # Authorization: only team owner can edit
    if team.user_id != current_user.id:
        flash("You can only edit your own team!", "danger")
        return redirect(url_for("teams_index"))

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

    # Get user's teams for "Add to Team" dropdown
    teams = Team.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "players/browse.html",
        players_qb=players_qb,
        players_rb=players_rb,
        players_wr=players_wr,
        players_te=players_te,
        teams=teams,
    )


@app.route("/teams/<int:team_id>/players/<int:player_id>/add", methods=["POST"])
@login_required
def players_add_to_team(team_id, player_id):
    team = Team.query.get_or_404(team_id)
    # Authorization: only team owner can add players
    if team.user_id != current_user.id:
        flash("You can only add players to your own team!", "danger")
        return redirect(url_for("teams_index"))

    player = Player.query.get_or_404(player_id)

    # Validation: ensure player is available (not already on a team)
    if player.team_id is not None:
        flash(f"{player.name} is already on a team!", "danger")
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
