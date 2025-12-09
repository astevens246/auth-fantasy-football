import unittest
from app import app, db
from models import User, Team, Player


class TestRoutes(unittest.TestCase):
    def setUp(self):
        """Executed prior to each test."""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["DEBUG"] = False
        app.config["SECRET_KEY"] = "test-secret-key"
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Executed after each test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def create_user(
        self, username="testuser", email="test@test.com", password="password123"
    ):
        user = User(username=username, email=email)
        user.set_password(password)
        with app.app_context():
            db.session.add(user)
            db.session.commit()
        return user

    # ========== TEST 1: Login Page (GET) ==========
    def test_login_page_loads(self):
        """Test that the login page loads successfully."""
        res = self.app.get("/login")
        self.assertEqual(res.status_code, 200)
        result_page_text = res.get_data(as_text=True)
        self.assertIn("Login", result_page_text)

    # ========== TEST 2: Login Success (POST) ==========
    def test_login_success(self):
        """Test that login works with correct credentials."""
        self.create_user(username="testuser", password="password123")
        form_data = {"username": "testuser", "password": "password123"}
        res = self.app.post("/login", data=form_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        result_page_text = res.get_data(as_text=True)
        self.assertIn("Teams", result_page_text)

    # ========== TEST 3: Login Failure (POST) ==========
    def test_login_failure(self):
        """Test that login fails with incorrect password."""
        self.create_user(username="testuser", password="password123")
        form_data = {"username": "testuser", "password": "wrongpassword"}
        res = self.app.post("/login", data=form_data)
        self.assertEqual(res.status_code, 200)
        result_page_text = res.get_data(as_text=True)
        self.assertIn("Invalid", result_page_text)

    # ========== TEST 4: Signup Success (POST) ==========
    def test_signup_success(self):
        """Test that signup creates a new user and logs them in."""
        form_data = {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "password123",
            "confirm_password": "password123",
        }
        res = self.app.post("/signup", data=form_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        result_page_text = res.get_data(as_text=True)
        self.assertIn("Teams", result_page_text)
        with app.app_context():
            user = User.query.filter_by(username="newuser").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, "newuser@test.com")

    # ========== TEST 5: Team Creation (POST) ==========
    def test_team_creation(self):
        """Test that a logged-in user can create a team."""
        self.create_user(username="testuser", password="password123")
        with app.app_context():
            user = User.query.filter_by(username="testuser").first()
            user_id = user.id
        login_data = {"username": "testuser", "password": "password123"}
        self.app.post("/login", data=login_data, follow_redirects=True)
        form_data = {"name": "My Test Team"}
        res = self.app.post("/teams/new", data=form_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        with app.app_context():
            team = Team.query.filter_by(name="My Test Team").first()
            self.assertIsNotNone(team)
            self.assertEqual(team.user_id, user_id)

    # ========== TEST 6: Authorization - Protected Route ==========
    def test_protected_route_redirects(self):
        """Test that protected routes redirect to login when not authenticated."""
        res = self.app.get("/teams", follow_redirects=True)
        result_page_text = res.get_data(as_text=True)
        self.assertIn("Login", result_page_text)


if __name__ == "__main__":
    unittest.main()
