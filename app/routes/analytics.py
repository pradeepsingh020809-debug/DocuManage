from flask import Blueprint, render_template, jsonify, g
from sqlalchemy import func
from app.models import db, Document, Folder, User, ActivityLog
from app.utils.decorators import login_required
from app.utils.helpers import format_file_size, get_category_color

dashboard_bp = Blueprint('dashboard', __name__)
analytics_bp = dashboard_bp

@analytics_bp.route('/dashboard')
@analytics_bp.route('/analytics')
@login_required
def index():
    """Main Analytics & Storage Dashboard."""
    user = g.current_user

    # Total counts
    total_docs = Document.query.filter_by(is_deleted=False).count()
    total_folders = Folder.query.filter_by(is_deleted=False).count()
    total_starred = Document.query.filter_by(is_starred=True, is_deleted=False).count()
    
    # Calculate storage
    total_bytes = db.session.query(func.sum(Document.file_size)).filter(Document.is_deleted == False).scalar() or 0

    # Category breakdown (count and bytes)
    category_data = db.session.query(
        Document.category,
        func.count(Document.id).label('count'),
        func.sum(Document.file_size).label('total_size')
    ).filter(Document.is_deleted == False).group_by(Document.category).all()

    breakdown = []
    for cat, count, size in category_data:
        size = size or 0
        percentage = round((size / total_bytes * 100), 1) if total_bytes > 0 else 0
        breakdown.append({
            'category': cat.title(),
            'raw_category': cat,
            'count': count,
            'size': size,
            'formatted_size': format_file_size(size),
            'percentage': percentage,
            'color': get_category_color(cat)
        })

    # Sort breakdown by size descending
    breakdown.sort(key=lambda x: x['size'], reverse=True)

    # Recent uploads (top 6)
    recent_docs = Document.query.filter_by(is_deleted=False).order_by(Document.created_at.desc()).limit(6).all()

    # Recent activity logs (top 10)
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()

    return render_template(
        'dashboard/index.html',
        total_docs=total_docs,
        total_folders=total_folders,
        total_starred=total_starred,
        total_bytes=total_bytes,
        formatted_total_bytes=format_file_size(total_bytes),
        breakdown=breakdown,
        recent_docs=recent_docs,
        recent_activities=recent_activities,
        user=user
    )

@analytics_bp.route('/api/analytics/storage')
@login_required
def storage_api():
    """API endpoint for charts."""
    total_bytes = db.session.query(func.sum(Document.file_size)).filter(Document.is_deleted == False).scalar() or 0
    category_data = db.session.query(
        Document.category,
        func.count(Document.id),
        func.sum(Document.file_size)
    ).filter(Document.is_deleted == False).group_by(Document.category).all()

    labels = []
    sizes = []
    colors = []
    counts = []

    for cat, count, size in category_data:
        labels.append(cat.title())
        sizes.append(size or 0)
        counts.append(count)
        colors.append(get_category_color(cat))

    return jsonify({
        'total_bytes': total_bytes,
        'formatted_total': format_file_size(total_bytes),
        'labels': labels,
        'sizes': sizes,
        'counts': counts,
        'colors': colors
    })
