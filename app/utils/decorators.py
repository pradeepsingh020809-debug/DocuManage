from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify, g
from app.models import db, User, ActivityLog

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required', 'success': False}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_active:
            session.clear()
            flash('Your account has been deactivated or not found.', 'danger')
            return redirect(url_for('auth.login'))
        
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Admin privileges required', 'success': False}), 403
            flash('Administrator privileges required for this action.', 'danger')
            return redirect(url_for('dashboard.index'))
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_manager:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Manager privileges required', 'success': False}), 403
            flash('Manager privileges required for this action.', 'danger')
            return redirect(url_for('dashboard.index'))
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def log_activity(action: str, document_id: int = None, folder_id: int = None, details: str = None, user_id: int = None):
    """Utility to append an audit trail activity log."""
    try:
        uid = user_id or session.get('user_id')
        ip = request.remote_addr if request else '127.0.0.1'
        log = ActivityLog(
            user_id=uid,
            action=action,
            document_id=document_id,
            folder_id=folder_id,
            details=details,
            ip_address=ip
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to log activity: {e}")
