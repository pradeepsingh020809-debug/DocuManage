import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, g, abort, current_app
from app.models import db, Document, DocumentVersion, Tag, Folder, Comment, ActivityLog
from app.services import FileService, MetadataService
from app.utils.decorators import login_required, log_activity
import markdown as md_parser

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

@documents_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    """Handles both AJAX multi-file uploads and standard form submissions."""
    files = request.files.getlist('files') or request.files.getlist('file')
    folder_id = request.form.get('folder_id')
    folder_id = int(folder_id) if folder_id and folder_id.isdigit() else None
    
    if not files or len(files) == 0 or (len(files) == 1 and not files[0].filename):
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'No files selected for upload.'}), 400
        flash('Please select at least one file to upload.', 'warning')
        return redirect(request.referrer or url_for('folders.explorer'))

    uploaded_docs = []
    user = g.current_user

    for file_obj in files:
        if not file_obj.filename:
            continue
        try:
            original_name, stored_name, file_path, file_size = FileService.save_upload(file_obj, user.id)
            sha256_hash = FileService.calculate_sha256(file_path)
            meta = MetadataService.extract_document_metadata(file_path, original_name)

            title = Path(original_name).stem
            description = request.form.get('description', '')

            doc = Document(
                title=title,
                description=description,
                filename=original_name,
                stored_filename=stored_name,
                file_path=str(file_path),
                file_size=file_size,
                mime_type=meta['mime_type'],
                file_extension=meta['file_extension'],
                category=meta['category'],
                checksum_sha256=sha256_hash,
                folder_id=folder_id,
                user_id=user.id,
                extracted_text=meta['extracted_text'],
                page_count=meta['page_count'],
                word_count=meta['word_count'],
                dimensions=meta['dimensions'],
                current_version=1
            )
            db.session.add(doc)
            db.session.flush() # Flush to get doc.id

            # Create initial version entry
            v1 = DocumentVersion(
                document_id=doc.id,
                version_number=1,
                filename=original_name,
                stored_filename=stored_name,
                file_path=str(file_path),
                file_size=file_size,
                checksum_sha256=sha256_hash,
                change_summary='Initial upload',
                uploaded_by_id=user.id
            )
            db.session.add(v1)

            # Update user storage used
            user.storage_used = (user.storage_used or 0) + file_size

            # Process tags if provided
            tags_str = request.form.get('tags', '')
            if tags_str:
                for tag_name in [t.strip() for t in tags_str.split(',') if t.strip()]:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    if tag not in doc.tags:
                        doc.tags.append(tag)

            log_activity('UPLOAD', document_id=doc.id, folder_id=folder_id, details=f"Uploaded {original_name} ({doc.formatted_size})")
            uploaded_docs.append(doc.to_dict())

        except Exception as e:
            db.session.rollback()
            print(f"Error uploading file {file_obj.filename}: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': f"Failed to upload {file_obj.filename}: {str(e)}"}), 500

    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'message': f"Successfully uploaded {len(uploaded_docs)} file(s).",
            'documents': uploaded_docs
        })

    flash(f"Successfully uploaded {len(uploaded_docs)} document(s).", 'success')
    if folder_id:
        return redirect(url_for('folders.explorer', folder_id=folder_id))
    return redirect(url_for('folders.explorer'))

@documents_bp.route('/<int:doc_id>')
@login_required
def details(doc_id):
    """Document details page with version history, metadata, comments, and audit trail."""
    doc = Document.query.get_or_404(doc_id)
    all_folders = Folder.query.filter_by(is_deleted=False).all()
    all_tags = Tag.query.order_by(Tag.name.asc()).all()
    
    # Audit trail for this document
    logs = ActivityLog.query.filter_by(document_id=doc.id).order_by(ActivityLog.created_at.desc()).limit(20).all()
    
    log_activity('VIEW', document_id=doc.id, details=f"Viewed document details for {doc.title}")
    return render_template('document/details.html', doc=doc, all_folders=all_folders, all_tags=all_tags, logs=logs)

@documents_bp.route('/<int:doc_id>/download')
@login_required
def download(doc_id):
    """Download the document or a specific version."""
    doc = Document.query.get_or_404(doc_id)
    version_num = request.args.get('version', type=int)

    file_path = doc.file_path
    filename = doc.filename

    if version_num and version_num != doc.current_version:
        ver = DocumentVersion.query.filter_by(document_id=doc.id, version_number=version_num).first()
        if ver:
            file_path = ver.file_path
            filename = ver.filename

    if not os.path.exists(file_path):
        flash('File not found on the server storage.', 'danger')
        return redirect(url_for('documents.details', doc_id=doc.id))

    log_activity('DOWNLOAD', document_id=doc.id, details=f"Downloaded {filename} (v{version_num or doc.current_version})")
    return send_file(file_path, as_attachment=True, download_name=filename)

@documents_bp.route('/<int:doc_id>/preview-data')
@login_required
def preview_data(doc_id):
    """Returns preview content/metadata for the universal in-browser previewer."""
    doc = Document.query.get_or_404(doc_id)
    
    if not os.path.exists(doc.file_path):
        return jsonify({'error': 'File not found on storage'}), 404

    category = doc.category
    ext = doc.file_extension.lower()

    data = {
        'id': doc.id,
        'title': doc.title,
        'filename': doc.filename,
        'category': category,
        'extension': ext,
        'mime_type': doc.mime_type,
        'size': doc.formatted_size,
        'version': doc.current_version,
        'stream_url': url_for('documents.stream', doc_id=doc.id),
        'download_url': url_for('documents.download', doc_id=doc.id)
    }

    # Markdown rendering
    if ext in ['md', 'markdown']:
        try:
            with open(doc.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                md_content = f.read(200000)
            data['rendered_html'] = md_parser.markdown(
                md_content,
                extensions=['fenced_code', 'tables', 'nl2br', 'codehilite']
            )
            data['raw_text'] = md_content
        except Exception as e:
            data['raw_text'] = f"Error reading markdown: {e}"

    # Text & Code files
    elif category in ['text', 'code'] or ext in ['txt', 'json', 'yaml', 'yml', 'py', 'js', 'html', 'css', 'sql', 'log', 'sh', 'xml', 'ts']:
        try:
            with open(doc.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data['raw_text'] = f.read(200000)
        except Exception as e:
            data['raw_text'] = f"Error reading text: {e}"

    # CSV / TSV spreadsheets
    elif ext in ['csv', 'tsv']:
        try:
            delimiter = '\t' if ext == 'tsv' else ','
            rows = []
            with open(doc.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for idx, line in enumerate(f):
                    if idx > 100: # Limit preview to first 100 rows
                        break
                    rows.append(line.rstrip('\r\n').split(delimiter))
            data['table_rows'] = rows
        except Exception as e:
            data['table_error'] = str(e)

    return jsonify(data)

@documents_bp.route('/<int:doc_id>/stream')
@login_required
def stream(doc_id):
    """Streams file for inline viewing (PDFs, Images, Audio, Video)."""
    doc = Document.query.get_or_404(doc_id)
    if not os.path.exists(doc.file_path):
        abort(404)
    return send_file(doc.file_path, mimetype=doc.mime_type, as_attachment=False)

@documents_bp.route('/<int:doc_id>/version', methods=['POST'])
@login_required
def new_version(doc_id):
    """Uploads a new version of the document."""
    doc = Document.query.get_or_404(doc_id)
    file_obj = request.files.get('file')
    summary = request.form.get('change_summary', '').strip() or f"Version {doc.current_version + 1}"

    if not file_obj or not file_obj.filename:
        flash('Please select a replacement file to upload as a new version.', 'warning')
        return redirect(url_for('documents.details', doc_id=doc.id))

    try:
        new_version_num = doc.current_version + 1
        orig_name, stored_name, dest_path, file_size = FileService.save_version_file(file_obj, doc.id, new_version_num)
        sha256_hash = FileService.calculate_sha256(dest_path)
        meta = MetadataService.extract_document_metadata(dest_path, orig_name)

        # Create new version record
        ver = DocumentVersion(
            document_id=doc.id,
            version_number=new_version_num,
            filename=orig_name,
            stored_filename=stored_name,
            file_path=str(dest_path),
            file_size=file_size,
            checksum_sha256=sha256_hash,
            change_summary=summary,
            uploaded_by_id=g.current_user.id
        )
        db.session.add(ver)

        # Update active document metadata to point to this new version
        size_delta = file_size - doc.file_size
        doc.filename = orig_name
        doc.stored_filename = stored_name
        doc.file_path = str(dest_path)
        doc.file_size = file_size
        doc.checksum_sha256 = sha256_hash
        doc.mime_type = meta['mime_type']
        doc.file_extension = meta['file_extension']
        doc.category = meta['category']
        doc.current_version = new_version_num
        doc.extracted_text = meta['extracted_text']
        doc.page_count = meta['page_count']
        doc.word_count = meta['word_count']
        doc.dimensions = meta['dimensions']
        doc.updated_at = datetime.now(timezone.utc)

        # Update user storage
        g.current_user.storage_used = (g.current_user.storage_used or 0) + size_delta

        db.session.commit()
        log_activity('NEW_VERSION', document_id=doc.id, details=f"Uploaded version {new_version_num}: {summary}")
        flash(f"Version {new_version_num} uploaded successfully!", 'success')

    except Exception as e:
        db.session.rollback()
        flash(f"Failed to upload new version: {e}", 'danger')

    return redirect(url_for('documents.details', doc_id=doc.id))

@documents_bp.route('/<int:doc_id>/rollback/<int:version_number>', methods=['POST'])
@login_required
def rollback_version(doc_id, version_number):
    """Roll back active document to a previous version."""
    doc = Document.query.get_or_404(doc_id)
    target_ver = DocumentVersion.query.filter_by(document_id=doc.id, version_number=version_number).first_or_404()

    try:
        # Create a new version that duplicates the target version's content
        new_version_num = doc.current_version + 1
        new_summary = f"Rolled back to Version {version_number}"

        ver = DocumentVersion(
            document_id=doc.id,
            version_number=new_version_num,
            filename=target_ver.filename,
            stored_filename=target_ver.stored_filename,
            file_path=target_ver.file_path,
            file_size=target_ver.file_size,
            checksum_sha256=target_ver.checksum_sha256,
            change_summary=new_summary,
            uploaded_by_id=g.current_user.id
        )
        db.session.add(ver)

        meta = MetadataService.extract_document_metadata(Path(target_ver.file_path), target_ver.filename)

        doc.filename = target_ver.filename
        doc.stored_filename = target_ver.stored_filename
        doc.file_path = target_ver.file_path
        doc.file_size = target_ver.file_size
        doc.checksum_sha256 = target_ver.checksum_sha256
        doc.mime_type = meta['mime_type']
        doc.file_extension = meta['file_extension']
        doc.category = meta['category']
        doc.current_version = new_version_num
        doc.extracted_text = meta['extracted_text']
        doc.page_count = meta['page_count']
        doc.word_count = meta['word_count']
        doc.dimensions = meta['dimensions']
        doc.updated_at = datetime.now(timezone.utc)

        db.session.commit()
        log_activity('ROLLBACK', document_id=doc.id, details=f"Rolled back to v{version_number} as v{new_version_num}")
        flash(f"Document restored to Version {version_number} state (as Version {new_version_num}).", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Rollback failed: {e}", 'danger')

    return redirect(url_for('documents.details', doc_id=doc.id))

@documents_bp.route('/<int:doc_id>/edit', methods=['POST'])
@login_required
def edit(doc_id):
    """Edit document title, description, folder, and tags."""
    doc = Document.query.get_or_404(doc_id)
    doc.title = request.form.get('title', doc.title).strip()
    doc.description = request.form.get('description', '').strip()
    
    new_folder_id = request.form.get('folder_id')
    if new_folder_id and new_folder_id.isdigit():
        doc.folder_id = int(new_folder_id)
    else:
        doc.folder_id = None

    # Handle tags
    tags_str = request.form.get('tags', '')
    doc.tags.clear()
    if tags_str:
        for t_name in [t.strip() for t in tags_str.split(',') if t.strip()]:
            tag = Tag.query.filter_by(name=t_name).first()
            if not tag:
                tag = Tag(name=t_name)
                db.session.add(tag)
            doc.tags.append(tag)

    doc.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    log_activity('EDIT_METADATA', document_id=doc.id, details=f"Updated metadata for {doc.title}")
    flash('Document details updated successfully.', 'success')
    return redirect(url_for('documents.details', doc_id=doc.id))

@documents_bp.route('/<int:doc_id>/star', methods=['POST'])
@login_required
def toggle_star(doc_id):
    """Toggle star / favorite on a document."""
    doc = Document.query.get_or_404(doc_id)
    doc.is_starred = not doc.is_starred
    db.session.commit()
    action = 'STAR' if doc.is_starred else 'UNSTAR'
    log_activity(action, document_id=doc.id, details=f"{'Starred' if doc.is_starred else 'Unstarred'} {doc.title}")
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'is_starred': doc.is_starred})
    return redirect(request.referrer or url_for('folders.explorer'))

@documents_bp.route('/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete(doc_id):
    """Soft delete to Trash."""
    doc = Document.query.get_or_404(doc_id)
    doc.is_deleted = True
    doc.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    log_activity('DELETE', document_id=doc.id, details=f"Moved {doc.title} to Trash")

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': f"'{doc.title}' moved to Trash."})
    flash(f"'{doc.title}' has been moved to Trash.", 'info')
    return redirect(request.referrer or url_for('folders.explorer'))

@documents_bp.route('/<int:doc_id>/restore', methods=['POST'])
@login_required
def restore(doc_id):
    """Restore document from Trash."""
    doc = Document.query.get_or_404(doc_id)
    doc.is_deleted = False
    doc.deleted_at = None
    db.session.commit()
    log_activity('RESTORE', document_id=doc.id, details=f"Restored {doc.title} from Trash")

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': f"'{doc.title}' restored."})
    flash(f"'{doc.title}' has been restored.", 'success')
    return redirect(url_for('folders.trash'))

@documents_bp.route('/<int:doc_id>/permanent-delete', methods=['POST'])
@login_required
def permanent_delete(doc_id):
    """Permanently deletes document, all versions, and physical files."""
    doc = Document.query.get_or_404(doc_id)
    title = doc.title

    # Delete physical files of all versions
    for ver in doc.versions:
        FileService.delete_physical_file(ver.file_path)
    FileService.delete_physical_file(doc.file_path)

    # Adjust user storage
    if doc.owner:
        doc.owner.storage_used = max(0, (doc.owner.storage_used or 0) - doc.file_size)

    log_activity('PERM_DELETE', details=f"Permanently deleted document '{title}'")
    db.session.delete(doc)
    db.session.commit()

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': f"'{title}' permanently deleted."})
    flash(f"'{title}' has been permanently deleted.", 'info')
    return redirect(url_for('folders.trash'))

@documents_bp.route('/<int:doc_id>/comment', methods=['POST'])
@login_required
def add_comment(doc_id):
    """Adds a comment / note to the document."""
    doc = Document.query.get_or_404(doc_id)
    content = request.form.get('content', '').strip()
    
    if content:
        comment = Comment(
            document_id=doc.id,
            user_id=g.current_user.id,
            content=content
        )
        db.session.add(comment)
        db.session.commit()
        log_activity('COMMENT', document_id=doc.id, details=f"Commented on {doc.title}")
        flash('Note added successfully.', 'success')

    return redirect(url_for('documents.details', doc_id=doc.id))
