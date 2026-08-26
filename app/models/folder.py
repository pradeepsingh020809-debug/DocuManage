from datetime import datetime, timezone
from app.models import db

class Folder(db.Model):
    __tablename__ = 'folders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256), nullable=True)
    color = db.Column(db.String(20), default='#6366f1')
    icon = db.Column(db.String(32), default='folder')
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Self-referencing relationship for nested hierarchy
    subfolders = db.relationship(
        'Folder',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    
    # Documents in this folder
    documents = db.relationship('Document', backref='folder', lazy='dynamic')

    def get_breadcrumbs(self):
        """Returns a list of dicts from root folder to this folder."""
        crumbs = []
        curr = self
        while curr:
            crumbs.insert(0, {'id': curr.id, 'name': curr.name})
            curr = curr.parent
        return crumbs

    def get_all_subfolder_ids(self):
        """Recursively get all descendant folder IDs."""
        ids = [self.id]
        children = Folder.query.filter_by(parent_id=self.id, is_deleted=False).all()
        for child in children:
            ids.extend(child.get_all_subfolder_ids())
        return ids

    def get_item_count(self):
        """Return total active folders + documents immediately inside this folder."""
        from app.models.document import Document
        sub_count = Folder.query.filter_by(parent_id=self.id, is_deleted=False).count()
        doc_count = Document.query.filter_by(folder_id=self.id, is_deleted=False).count()
        return sub_count + doc_count

    def get_total_size(self):
        """Return total bytes of active documents in this folder and subfolders."""
        from app.models.document import Document
        all_ids = self.get_all_subfolder_ids()
        docs = Document.query.filter(Document.folder_id.in_(all_ids), Document.is_deleted == False).all()
        return sum(d.file_size or 0 for d in docs)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'parent_id': self.parent_id,
            'user_id': self.user_id,
            'item_count': self.get_item_count(),
            'total_size': self.get_total_size(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'breadcrumbs': self.get_breadcrumbs()
        }
