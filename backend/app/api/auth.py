"""
Authentication API endpoints
Sign up, sign in, logout
"""
from flask import Blueprint, request, jsonify
from typing import Dict, Any
from ..models.user import UserDatabase

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Global user database (in production, use proper database)
user_db = UserDatabase()


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Create new user account
    
    Request body:
    {
        "username": "user123",
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username or len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        if not email or '@' not in email:
            return jsonify({'error': 'Invalid email address'}), 400
        
        if not password or len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Create user
        user = user_db.create_user(username, email, password)
        
        if not user:
            return jsonify({'error': 'Username or email already exists'}), 409
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@auth_bp.route('/signin', methods=['POST'])
def signin():
    """
    Sign in user
    
    Request body:
    {
        "username": "user123",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Authenticate
        session = user_db.authenticate(username, password)
        
        if not session:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Get user info
        user = user_db.get_user_by_username(username)
        
        return jsonify({
            'success': True,
            'message': 'Signed in successfully',
            'token': session.token,
            'user': user.to_dict(),
            'expires_at': session.expires_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout user
    
    Headers:
        Authorization: Bearer <token>
    """
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Invalid authorization header'}), 401
        
        token = auth_header[7:]  # Remove 'Bearer '
        
        # Logout
        success = user_db.logout(token)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Logged out successfully'
            }), 200
        else:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """
    Verify session token
    
    Headers:
        Authorization: Bearer <token>
    """
    try:
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Invalid authorization header'}), 401
        
        token = auth_header[7:]
        
        user = user_db.verify_session(token)
        
        if user:
            return jsonify({
                'valid': True,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'valid': False}), 401
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """
    Get user profile and statistics
    
    Headers:
        Authorization: Bearer <token>
    """
    try:
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Invalid authorization header'}), 401
        
        token = auth_header[7:]
        user = user_db.verify_session(token)
        
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        stats = user_db.get_user_stats(user.username)
        
        return jsonify({
            'success': True,
            'profile': stats
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


def require_auth(func):
    """
    Decorator to require authentication
    Adds 'user' to kwargs
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header[7:]
        user = user_db.verify_session(token)
        
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        kwargs['user'] = user
        return func(*args, **kwargs)
    
    return wrapper


def get_user_db() -> UserDatabase:
    """Get global user database instance"""
    return user_db
