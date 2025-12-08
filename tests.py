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


if __name__ == '__main__':
    unittest.main()

