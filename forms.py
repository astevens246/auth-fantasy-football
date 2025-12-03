from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length
from models import User


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class SignupForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=20)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already exists.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email already exists.")


class TeamForm(FlaskForm):
    name = StringField("Team Name", validators=[DataRequired(), Length(min=3, max=100)])
    submit = SubmitField("Create Team")
