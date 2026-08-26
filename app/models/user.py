from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='editor', nullable=False) # admin, manager, editor, viewer
    avatar_color = db.Column(db.String(20), default='#6366f1')
    is_active = db.Column(db.Boolean, default=True)
    storage_used = db.Column(db.BigInteger, default=0) # in bytes
    storage_quota = db.Column(db.BigInteger, default=5 * 1024 * 1024 * 1024) # 5 GB default
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    documents = db.relationship('Document', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    folders = db.relationship('Folder', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

    @property
    def is_manager(self) -> bool:
        return self.role in ['admin', 'manager']

    @property
    def can_edit(self) -> bool:
        return self.role in ['admin', 'manager', 'editor']

    @property
    def can_delete(self) -> bool:
        return self.role in ['admin', 'manager', 'editor']

    @property
    def initials(self) -> str:
        parts = self.full_name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return self.username[:2].upper()

    @property
    def storage_percentage(self) -> float:
        if not self.storage_quota or self.storage_quota == 0:
            return 0.0
        return min(100.0, round((self.storage_used / self.storage_quota) * 100, 1))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'avatar_color': self.avatar_color,
            'storage_used': self.storage_used,
            'storage_quota': self.storage_quota,
            'storage_percentage': self.storage_percentage,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
