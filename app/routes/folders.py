from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app.models import db, Folder, Document, Tag, DocumentShare
from app.utils.decorators import login_required, log_activity

folders_bp = Blueprint('folders', __name__)

FOLDER_COLORS = ['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#64748b']

@folders_bp.route('/')
@folders_bp.route('/explorer')
@folders_bp.route('/explorer/<int:folder_id>')
@login_required
def explorer(folder_id=None):
    """Main document and folder explorer interface."""
    current_folder = None
    breadcrumbs = []

    if folder_id:
        current_folder = Folder.query.get_or_404(folder_id)
        if current_folder.is_deleted:
            flash('This folder is in the Trash.', 'warning')
            return redirect(url_for('folders.trash'))
        breadcrumbs = current_folder.get_breadcrumbs()

    # Query active subfolders in current folder
    subfolders_query = Folder.query.filter_by(
        parent_id=folder_id,
        is_deleted=False
    ).order_by(Folder.name.asc())
    subfolders = subfolders_query.all()

    # Query active documents in current folder
    docs_query = Document.query.filter_by(
        folder_id=folder_id,
        is_deleted=False
    )

    # Filter by category if requested
    category_filter = request.args.get('category')
    if category_filter and category_filter != 'all':
        docs_query = docs_query.filter(Document.category == category_filter)

    # Filter by tag if requested
    tag_id = request.args.get('tag_id', type=int)
    if tag_id:
        docs_query = docs_query.filter(Document.tags.any(Tag.id == tag_id))

    # Sorting
    sort_by = request.args.get('sort', 'date_desc')
    if sort_by == 'name_asc':
        docs_query = docs_query.order_by(Document.title.asc())
    elif sort_by == 'name_desc':
        docs_query = docs_query.order_by(Document.title.desc())
    elif sort_by == 'size_desc':
        docs_query = docs_query.order_by(Document.file_size.desc())
    elif sort_by == 'size_asc':
        docs_query = docs_query.order_by(Document.file_size.asc())
    elif sort_by == 'date_asc':
        docs_query = docs_query.order_by(Document.updated_at.asc())
    else: # date_desc
        docs_query = docs_query.order_by(Document.updated_at.desc())

    documents = docs_query.all()

    # All folders for move/copy modals
    all_folders = Folder.query.filter_by(is_deleted=False).all()
    all_tags = Tag.query.order_by(Tag.name.asc()).all()

    # View layout preference (grid or list)
    view_mode = request.args.get('view', 'grid')

    return render_template(
        'explorer/index.html',
        current_folder=current_folder,
        breadcrumbs=breadcrumbs,
        subfolders=subfolders,
        documents=documents,
        all_folders=all_folders,
        all_tags=all_tags,
        view_mode=view_mode,
        selected_category=category_filter or 'all',
        selected_tag=tag_id,
        sort_by=sort_by,
        folder_colors=FOLDER_COLORS
    )

@folders_bp.route('/folder/create', methods=['POST'])
@login_required
def create_folder():
    """Create a new folder."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    color = request.form.get('color', '#6366f1')
    parent_id = request.form.get('parent_id')
    parent_id = int(parent_id) if parent_id and parent_id.isdigit() else None

    if not name:
        flash('Folder name is required.', 'warning')
        return redirect(request.referrer or url_for('folders.explorer'))

    folder = Folder(
        name=name,
        description=description,
        color=color,
        parent_id=parent_id,
        user_id=g.current_user.id
    )
    db.session.add(folder)
    db.session.commit()

    log_activity('CREATE_FOLDER', folder_id=folder.id, details=f"Created folder '{name}'")
    flash(f"Folder '{name}' created successfully.", 'success')

    if parent_id:
        return redirect(url_for('folders.explorer', folder_id=parent_id))
    return redirect(url_for('folders.explorer'))

@folders_bp.route('/folder/<int:folder_id>/rename', methods=['POST'])
@login_required
def rename_folder(folder_id):
    """Rename an existing folder."""
    folder = Folder.query.get_or_404(folder_id)
    new_name = request.form.get('name', '').strip()
    new_color = request.form.get('color', folder.color)
    new_desc = request.form.get('description', folder.description)

    if new_name:
        folder.name = new_name
        folder.color = new_color
        folder.description = new_desc
        db.session.commit()
        log_activity('RENAME', folder_id=folder.id, details=f"Renamed folder to '{new_name}'")
        flash('Folder updated successfully.', 'success')

    return redirect(request.referrer or url_for('folders.explorer', folder_id=folder.id))

@folders_bp.route('/folder/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete_folder(folder_id):
    """Soft delete folder and its contents to Trash."""
    folder = Folder.query.get_or_404(folder_id)
    folder.is_deleted = True
    folder.deleted_at = datetime.now(timezone.utc)

    # Soft delete subfolders and documents inside
    sub_ids = folder.get_all_subfolder_ids()
    Folder.query.filter(Folder.id.in_(sub_ids)).update({
        'is_deleted': True,
        'deleted_at': datetime.now(timezone.utc)
    }, synchronize_session=False)

    Document.query.filter(Document.folder_id.in_(sub_ids)).update({
        'is_deleted': True,
        'deleted_at': datetime.now(timezone.utc)
    }, synchronize_session=False)

    db.session.commit()
    log_activity('DELETE', folder_id=folder.id, details=f"Moved folder '{folder.name}' and contents to Trash")
    flash(f"Folder '{folder.name}' and its contents moved to Trash.", 'info')

    if folder.parent_id:
        return redirect(url_for('folders.explorer', folder_id=folder.parent_id))
    return redirect(url_for('folders.explorer'))

@folders_bp.route('/trash')
@login_required
def trash():
    """Recycle bin view showing soft-deleted files and folders."""
    deleted_folders = Folder.query.filter_by(is_deleted=True).order_by(Folder.deleted_at.desc()).all()
    deleted_docs = Document.query.filter_by(is_deleted=True).order_by(Document.deleted_at.desc()).all()
    return render_template('explorer/trash.html', deleted_folders=deleted_folders, deleted_docs=deleted_docs)

@folders_bp.route('/starred')
@login_required
def starred():
    """Starred / Favorites list view."""
    starred_docs = Document.query.filter_by(is_starred=True, is_deleted=False).order_by(Document.updated_at.desc()).all()
    return render_template('explorer/starred.html', documents=starred_docs)

@folders_bp.route('/shared')
@login_required
def shared():
    """Shared documents view."""
    user_shares = DocumentShare.query.filter_by(created_by_id=g.current_user.id).order_by(DocumentShare.created_at.desc()).all()
    return render_template('explorer/shared.html', shares=user_shares)

@folders_bp.route('/trash/empty', methods=['POST'])
@login_required
def empty_trash():
    """Permanently delete all items currently in Trash."""
    from app.services import FileService

    deleted_docs = Document.query.filter_by(is_deleted=True).all()
    for doc in deleted_docs:
        for ver in doc.versions:
            FileService.delete_physical_file(ver.file_path)
        FileService.delete_physical_file(doc.file_path)
        if doc.owner:
            doc.owner.storage_used = max(0, (doc.owner.storage_used or 0) - doc.file_size)
        db.session.delete(doc)

    deleted_folders = Folder.query.filter_by(is_deleted=True).all()
    for f in deleted_folders:
        db.session.delete(f)

    db.session.commit()
    log_activity('EMPTY_TRASH', details="Emptied all items in Trash")
    flash('Trash emptied permanently.', 'success')
    return redirect(url_for('folders.trash'))
