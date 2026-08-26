import os
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, g, session, abort
from app.models import db, Document, DocumentShare
from app.utils.decorators import login_required, log_activity

share_bp = Blueprint('share', __name__)

@share_bp.route('/share/create/<int:doc_id>', methods=['POST'])
@login_required
def create_share(doc_id):
    """Generate a share link for a document with optional password and expiration."""
    doc = Document.query.get_or_404(doc_id)
    
    expires_in_days = request.form.get('expires_in_days', type=int)
    password = request.form.get('password', '').strip()
    allow_download = bool(request.form.get('allow_download', True))

    expires_at = None
    if expires_in_days and expires_in_days > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    share = DocumentShare(
        document_id=doc.id,
        created_by_id=g.current_user.id,
        expires_at=expires_at,
        allow_download=allow_download
    )
    if password:
        share.set_password(password)

    db.session.add(share)
    db.session.commit()

    log_activity('SHARE', document_id=doc.id, details=f"Created share link for {doc.title}")
    
    share_url = url_for('share.view_shared', token=share.share_token, _external=True)

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'share_url': share_url,
            'token': share.share_token,
            'has_password': bool(password),
            'expires_at': share.expires_at.isoformat() if share.expires_at else None
        })

    flash('Share link generated successfully!', 'success')
    return redirect(url_for('documents.details', doc_id=doc.id))

@share_bp.route('/share/revoke/<int:share_id>', methods=['POST'])
@login_required
def revoke_share(share_id):
    """Revoke an active share link."""
    share = DocumentShare.query.get_or_404(share_id)
    doc_id = share.document_id
    db.session.delete(share)
    db.session.commit()
    log_activity('REVOKE_SHARE', document_id=doc_id, details="Revoked share link")
    flash('Share link has been revoked.', 'info')
    return redirect(request.referrer or url_for('documents.details', doc_id=doc_id))

@share_bp.route('/s/<token>', methods=['GET'])
def view_shared(token):
    """Public landing page to view or download a shared document."""
    share = DocumentShare.query.filter_by(share_token=token).first_or_404()
    doc = share.document

    if share.is_expired:
        return render_template('document/share_public.html', share=share, doc=doc, expired=True)

    # Check password protection
    if share.password_hash:
        unlocked_tokens = session.get('unlocked_shares', [])
        if token not in unlocked_tokens:
            return render_template('document/share_public.html', share=share, doc=doc, requires_password=True)

    # Update access count
    share.access_count = (share.access_count or 0) + 1
    db.session.commit()

    return render_template('document/share_public.html', share=share, doc=doc, requires_password=False)

@share_bp.route('/s/<token>/unlock', methods=['POST'])
def unlock_shared(token):
    """Verify password for protected share link."""
    share = DocumentShare.query.filter_by(share_token=token).first_or_404()
    password = request.form.get('password', '')

    if share.check_password(password):
        unlocked = session.get('unlocked_shares', [])
        if token not in unlocked:
            unlocked.append(token)
            session['unlocked_shares'] = unlocked
        return redirect(url_for('share.view_shared', token=token))
    
    flash('Incorrect password. Please try again.', 'danger')
    return render_template('document/share_public.html', share=share, doc=share.document, requires_password=True)

@share_bp.route('/s/<token>/download')
def download_shared(token):
    """Public download endpoint for shared document."""
    share = DocumentShare.query.filter_by(share_token=token).first_or_404()
    doc = share.document

    if share.is_expired or not share.allow_download:
        abort(403)

    if share.password_hash:
        unlocked_tokens = session.get('unlocked_shares', [])
        if token not in unlocked_tokens:
            abort(401)

    if not os.path.exists(doc.file_path):
        abort(404)

    return send_file(doc.file_path, as_attachment=True, download_name=doc.filename)
