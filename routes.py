from flask import render_template, redirect, url_for, flash, request
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
    # Query: get all players where team_id is None
    players = Player.query.filter_by(team_id=None).all()
    return render_template("players/browse.html", players=players)


@app.route("/teams/<int:team_id>/players/<int:player_id>/add", methods=["POST"])
@login_required
def players_add_to_team(team_id, player_id):
    team = Team.query.get_or_404(team_id)
    # Authorization: only team owner can add players
    if team.user_id != current_user.id:
        flash("You can only add players to your own team!", "danger")
        return redirect(url_for("teams_index"))

    player = Player.query.get_or_404(player_id)
    # Add player to team
    player.team_id = team_id
    db.session.commit()
    flash(f"{player.name} added to {team.name}!", "success")
    return redirect(url_for("teams_show", id=team_id))


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
