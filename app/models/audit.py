from datetime import datetime, timezone
from app.models import db

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(64), nullable=False, index=True) 
    # e.g. UPLOAD, DOWNLOAD, VIEW, DELETE, RESTORE, PERM_DELETE, NEW_VERSION, ROLLBACK, RENAME, MOVE, SHARE, COMMENT
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True, index=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id', ondelete='SET NULL'), nullable=True, index=True)
    details = db.Column(db.String(512), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    folder = db.relationship('Folder', foreign_keys=[folder_id])

    @property
    def action_badge_color(self) -> str:
        mapping = {
            'UPLOAD': 'badge-success',
            'DOWNLOAD': 'badge-primary',
            'VIEW': 'badge-secondary',
            'DELETE': 'badge-danger',
            'RESTORE': 'badge-warning',
            'PERM_DELETE': 'badge-danger',
            'NEW_VERSION': 'badge-info',
            'ROLLBACK': 'badge-warning',
            'RENAME': 'badge-secondary',
            'MOVE': 'badge-secondary',
            'SHARE': 'badge-info',
            'COMMENT': 'badge-primary',
            'LOGIN': 'badge-success',
            'REGISTER': 'badge-success'
        }
        return mapping.get(self.action, 'badge-secondary')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else 'System',
            'action': self.action,
            'action_badge_color': self.action_badge_color,
            'document_id': self.document_id,
            'document_title': self.document.title if self.document else None,
            'folder_id': self.folder_id,
            'folder_name': self.folder.name if self.folder else None,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'user_id': self.user_id,
            'author_name': self.author.full_name if self.author else 'Unknown',
            'author_initials': self.author.initials if self.author else '??',
            'author_avatar_color': self.author.avatar_color if self.author else '#6366f1',
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
