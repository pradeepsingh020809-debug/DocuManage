import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db

# Many-to-Many association table for Document <-> Tag
document_tags = db.Table(
    'document_tags',
    db.Column('document_id', db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    color = db.Column(db.String(20), default='#6366f1')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color
        }

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(256), nullable=False) # original uploaded name
    stored_filename = db.Column(db.String(256), nullable=False) # disk name
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.BigInteger, default=0, nullable=False)
    mime_type = db.Column(db.String(128), default='application/octet-stream')
    file_extension = db.Column(db.String(20), default='', index=True)
    category = db.Column(db.String(32), default='document', index=True) # pdf, document, spreadsheet, presentation, image, text, code, archive, audio, video
    checksum_sha256 = db.Column(db.String(64), nullable=True)
    
    # Organization
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id', ondelete='SET NULL'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Status flags
    is_starred = db.Column(db.Boolean, default=False, index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Versioning
    current_version = db.Column(db.Integer, default=1, nullable=False)
    
    # Content & Metadata Extraction (for full-text search)
    extracted_text = db.Column(db.Text, nullable=True)
    page_count = db.Column(db.Integer, nullable=True)
    word_count = db.Column(db.Integer, nullable=True)
    dimensions = db.Column(db.String(32), nullable=True) # e.g. "1920x1080"
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    tags = db.relationship('Tag', secondary=document_tags, lazy='subquery', backref=db.backref('documents', lazy=True))
    versions = db.relationship('DocumentVersion', backref='document', lazy='dynamic', cascade='all, delete-orphan', order_by='desc(DocumentVersion.version_number)')
    shares = db.relationship('DocumentShare', backref='document', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='document', lazy='dynamic', cascade='all, delete-orphan', order_by='desc(Comment.created_at)')
    activity_logs = db.relationship('ActivityLog', backref='document', lazy='dynamic')

    @property
    def formatted_size(self) -> str:
        from app.utils.helpers import format_file_size
        return format_file_size(self.file_size)

    @property
    def is_previewable(self) -> bool:
        from app.config import Config
        return self.file_extension.lower() in Config.PREVIEW_EXTENSIONS

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'filename': self.filename,
            'file_size': self.file_size,
            'formatted_size': self.formatted_size,
            'mime_type': self.mime_type,
            'file_extension': self.file_extension,
            'category': self.category,
            'checksum_sha256': self.checksum_sha256,
            'folder_id': self.folder_id,
            'user_id': self.user_id,
            'owner_name': self.owner.full_name if self.owner else 'Unknown',
            'is_starred': self.is_starred,
            'is_deleted': self.is_deleted,
            'current_version': self.current_version,
            'page_count': self.page_count,
            'word_count': self.word_count,
            'is_previewable': self.is_previewable,
            'tags': [t.to_dict() for t in self.tags],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DocumentVersion(db.Model):
    __tablename__ = 'document_versions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    stored_filename = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.BigInteger, default=0, nullable=False)
    checksum_sha256 = db.Column(db.String(64), nullable=True)
    change_summary = db.Column(db.String(512), nullable=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    uploader = db.relationship('User', foreign_keys=[uploaded_by_id])

    @property
    def formatted_size(self) -> str:
        from app.utils.helpers import format_file_size
        return format_file_size(self.file_size)

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'version_number': self.version_number,
            'filename': self.filename,
            'file_size': self.file_size,
            'formatted_size': self.formatted_size,
            'checksum_sha256': self.checksum_sha256,
            'change_summary': self.change_summary,
            'uploaded_by': self.uploader.full_name if self.uploader else 'Unknown',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DocumentShare(db.Model):
    __tablename__ = 'document_shares'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    share_token = db.Column(db.String(64), unique=True, default=lambda: uuid.uuid4().hex, index=True)
    is_public = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(256), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    allow_download = db.Column(db.Boolean, default=True)
    access_count = db.Column(db.Integer, default=0)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    creator = db.relationship('User', foreign_keys=[created_by_id])

    def set_password(self, password: str):
        if password:
            self.password_hash = generate_password_hash(password)
        else:
            self.password_hash = None

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return True
        return check_password_hash(self.password_hash, password)

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        # Normalize timezone
        now = datetime.now(timezone.utc)
        exp = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return now > exp

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'share_token': self.share_token,
            'is_public': self.is_public,
            'has_password': bool(self.password_hash),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired,
            'allow_download': self.allow_download,
            'access_count': self.access_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
