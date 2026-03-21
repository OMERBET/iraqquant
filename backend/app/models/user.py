"""
User Model - bcrypt hashing + persistent sessions
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict

try:
    import bcrypt
    _BCRYPT = True
except ImportError:
    import hashlib
    _BCRYPT = False


def _hash_pw(password: str) -> str:
    if _BCRYPT:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_pw(password: str, hashed: str) -> bool:
    if _BCRYPT:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest() == hashed


class User:
    def __init__(self, username, email, password_hash,
                 created_at=None, user_id=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.utcnow()
        self.user_id = user_id or secrets.token_urlsafe(16)
        self.is_active = True
        self.job_count = 0
        self.total_qubits_used = 0

    @staticmethod
    def hash_password(password: str) -> str:
        return _hash_pw(password)

    def verify_password(self, password: str) -> bool:
        return _verify_pw(password, self.password_hash)

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'job_count': self.job_count,
            'total_qubits_used': self.total_qubits_used,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        u = cls(data['username'], data['email'], data['password_hash'],
                created_at=datetime.fromisoformat(data.get('created_at', datetime.utcnow().isoformat())),
                user_id=data.get('user_id'))
        u.is_active = data.get('is_active', True)
        u.job_count = data.get('job_count', 0)
        u.total_qubits_used = data.get('total_qubits_used', 0)
        return u


class Session:
    def __init__(self, user_id: str, token: Optional[str] = None):
        self.user_id = user_id
        self.token = token or secrets.token_urlsafe(32)
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(days=7)
        self.last_activity = datetime.utcnow()

    def is_valid(self) -> bool:
        return datetime.utcnow() < self.expires_at

    def refresh(self):
        self.last_activity = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(days=7)

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'token': self.token,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
        }


class UserDatabase:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self.emails: Dict[str, str] = {}

    def create_user(self, username, email, password) -> Optional[User]:
        if username in self.users or email in self.emails:
            return None
        user = User(username, email, User.hash_password(password))
        self.users[username] = user
        self.emails[email] = username
        return user

    def authenticate(self, username, password) -> Optional[Session]:
        user = self.users.get(username)
        if not user or not user.is_active or not user.verify_password(password):
            return None
        session = Session(user.user_id)
        self.sessions[session.token] = session
        return session

    def verify_session(self, token) -> Optional[User]:
        session = self.sessions.get(token)
        if not session or not session.is_valid():
            return None
        session.refresh()
        return next((u for u in self.users.values() if u.user_id == session.user_id), None)

    def logout(self, token) -> bool:
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False

    def get_user_by_username(self, username) -> Optional[User]:
        return self.users.get(username)

    def get_user_stats(self, username) -> Optional[Dict]:
        user = self.users.get(username)
        if not user:
            return None
        return {
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'job_count': user.job_count,
            'total_qubits_used': user.total_qubits_used,
            'active_sessions': sum(1 for s in self.sessions.values()
                                   if s.user_id == user.user_id and s.is_valid()),
        }
