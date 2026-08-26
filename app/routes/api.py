from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g, send_file
from app.models import db, Document, Folder, Tag
from app.services import FileService
from app.utils.decorators import login_required, log_activity

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/documents/batch-delete', methods=['POST'])
@login_required
def batch_delete():
    """Soft-deletes a list of document IDs."""
    data = request.get_json() or {}
    doc_ids = data.get('doc_ids', [])
    if not doc_ids:
        return jsonify({'error': 'No document IDs provided', 'success': False}), 400

    docs = Document.query.filter(Document.id.in_(doc_ids)).all()
    for doc in docs:
        doc.is_deleted = True
        doc.deleted_at = datetime.now(timezone.utc)
    
    db.session.commit()
    log_activity('BATCH_DELETE', details=f"Moved {len(docs)} document(s) to Trash")
    return jsonify({'success': True, 'count': len(docs), 'message': f'{len(docs)} item(s) moved to Trash.'})

@api_bp.route('/documents/batch-move', methods=['POST'])
@login_required
def batch_move():
    """Moves a list of documents to a target folder."""
    data = request.get_json() or {}
    doc_ids = data.get('doc_ids', [])
    target_folder_id = data.get('folder_id')
    target_folder_id = int(target_folder_id) if target_folder_id and str(target_folder_id).isdigit() else None

    if not doc_ids:
        return jsonify({'error': 'No documents selected', 'success': False}), 400

    docs = Document.query.filter(Document.id.in_(doc_ids)).all()
    for doc in docs:
        doc.folder_id = target_folder_id
    
    db.session.commit()
    target_folder = db.session.get(Folder, target_folder_id) if target_folder_id else None
    dest_name = target_folder.name if target_folder else 'Root'
    log_activity('BATCH_MOVE', details=f"Moved {len(docs)} document(s) to '{dest_name}'")
    return jsonify({'success': True, 'count': len(docs), 'message': f'{len(docs)} item(s) moved to {dest_name}.'})

@api_bp.route('/documents/batch-download', methods=['POST'])
@login_required
def batch_download():
    """Bundles selected documents into a ZIP archive and triggers download."""
    doc_ids = request.form.getlist('doc_ids')
    if not doc_ids:
        data = request.get_json() or {}
        doc_ids = data.get('doc_ids', [])

    if not doc_ids:
        return jsonify({'error': 'No documents selected', 'success': False}), 400

    docs = Document.query.filter(Document.id.in_(doc_ids), Document.is_deleted == False).all()
    if not docs:
        return jsonify({'error': 'No valid documents found to download', 'success': False}), 404

    zip_io = FileService.create_zip_archive(docs)
    log_activity('BATCH_DOWNLOAD', details=f"Downloaded ZIP archive of {len(docs)} documents")
    return send_file(
        zip_io,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"DocuVault_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    )

@api_bp.route('/tags', methods=['GET'])
@login_required
def get_tags():
    """Returns list of all available tags."""
    tags = Tag.query.order_by(Tag.name.asc()).all()
    return jsonify({'tags': [t.to_dict() for t in tags]})
