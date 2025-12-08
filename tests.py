import unittest
from app import app, db
from models import User, Team, Player


class TestRoutes(unittest.TestCase):
    def setUp(self):
        """Executed prior to each test."""
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['DEBUG'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'  # Needed for sessions (login)
        # Use in-memory database so we start fresh each time
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        # Create the test client
        self.app = app.test_client()
        
        # Create all tables in the in-memory database
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Executed after each test."""
        # Clean up the database after each test
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    # Helper function to create a test user
    def create_user(self, username='testuser', email='test@test.com', password='password123'):
        """Helper function to create a user for testing."""
        user = User(username=username, email=email)
        user.set_password(password)
        with app.app_context():
            db.session.add(user)
            db.session.commit()
        return user
    
    # ========== TEST 1: Login Page (GET) ==========
    def test_login_page_loads(self):
        """Test that the login page loads successfully."""
        # SCENARIO: Make a GET request to /login
        res = self.app.get('/login')
        
        # EXPECTATION: Status code should be 200 (success)
        # ACTUAL: res.status_code
        # COMPARISON: assertEqual checks if they match
        self.assertEqual(res.status_code, 200)
        
        # EXPECTATION: Page should contain "Login" text
        # ACTUAL: Get the page content as text
        result_page_text = res.get_data(as_text=True)
        # COMPARISON: assertIn checks if "Login" is in the page
        self.assertIn('Login', result_page_text)
    
    # ========== TEST 2: Login Success (POST) ==========
    def test_login_success(self):
        """Test that login works with correct credentials."""
        # SCENARIO: First, create a user in the database
        self.create_user(username='testuser', password='password123')
        
        # SCENARIO: Make a POST request to /login with form data
        # For POST requests, we pass data as a dictionary
        form_data = {
            'username': 'testuser',
            'password': 'password123'
        }
        res = self.app.post('/login', data=form_data, follow_redirects=True)
        
        # EXPECTATION: Status code should be 200 (success)
        # ACTUAL: res.status_code
        self.assertEqual(res.status_code, 200)
        
        # EXPECTATION: After successful login, should redirect to teams page
        # ACTUAL: Check the page content
        result_page_text = res.get_data(as_text=True)
        # We expect to see something from the teams page (like "Teams" or team-related content)
        # This confirms we were redirected after login
        self.assertIn('Teams', result_page_text)
    
    # ========== TEST 3: Login Failure (POST) ==========
    def test_login_failure(self):
        """Test that login fails with incorrect password."""
        # SCENARIO: Create a user with password 'password123'
        self.create_user(username='testuser', password='password123')
        
        # SCENARIO: Try to login with wrong password
        form_data = {
            'username': 'testuser',
            'password': 'wrongpassword'  # Wrong password!
        }
        res = self.app.post('/login', data=form_data)
        
        # EXPECTATION: Status code should be 200 (page loads, but login fails)
        self.assertEqual(res.status_code, 200)
        
        # EXPECTATION: Should show error message
        result_page_text = res.get_data(as_text=True)
        # Check for the error flash message
        self.assertIn('Invalid', result_page_text)
    
    # ========== TEST 4: Signup Success (POST) ==========
    def test_signup_success(self):
        """Test that signup creates a new user and logs them in."""
        # SCENARIO: Make a POST request to /signup with form data
        form_data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123',
            'confirm_password': 'password123'  # Must match password
        }
        res = self.app.post('/signup', data=form_data, follow_redirects=True)
        
        # EXPECTATION: Status code should be 200
        self.assertEqual(res.status_code, 200)
        
        # EXPECTATION: Should redirect to teams page after signup
        result_page_text = res.get_data(as_text=True)
        self.assertIn('Teams', result_page_text)
        
        # EXPECTATION: User should be created in database
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)  # User should exist
            self.assertEqual(user.email, 'newuser@test.com')
    
    # ========== TEST 5: Team Creation (POST) ==========
    def test_team_creation(self):
        """Test that a logged-in user can create a team."""
        # SCENARIO: Create a user and log them in
        self.create_user(username='testuser', password='password123')
        
        # Get user ID from database
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            user_id = user.id
        
        # Login first
        login_data = {
            'username': 'testuser',
            'password': 'password123'
        }
        self.app.post('/login', data=login_data, follow_redirects=True)
        
        # SCENARIO: Create a team via POST request
        form_data = {
            'name': 'My Test Team'
        }
        res = self.app.post('/teams/new', data=form_data, follow_redirects=True)
        
        # EXPECTATION: Status code should be 200
        self.assertEqual(res.status_code, 200)
        
        # EXPECTATION: Team should be created in database
        with app.app_context():
            team = Team.query.filter_by(name='My Test Team').first()
            self.assertIsNotNone(team)  # Team should exist
            self.assertEqual(team.user_id, user_id)  # Team should belong to the user
    
    # ========== TEST 6: Authorization - Protected Route ==========
    def test_protected_route_redirects(self):
        """Test that protected routes redirect to login when not authenticated."""
        # SCENARIO: Try to access /teams without logging in
        res = self.app.get('/teams', follow_redirects=True)
        
        # EXPECTATION: Should redirect to login page
        # ACTUAL: Check the page content
        result_page_text = res.get_data(as_text=True)
        # Should see login page content
        self.assertIn('Login', result_page_text)


if __name__ == '__main__':
    unittest.main()

