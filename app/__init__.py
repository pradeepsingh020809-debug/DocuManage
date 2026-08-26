import os
from flask import Flask, session, g, render_template, request
from app.config import Config
from app.models import db, User, Folder
from app.services import FileService
from app.utils.helpers import format_file_size, time_ago, get_file_icon, get_category_color

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Ensure storage paths exist
    FileService.ensure_storage_dirs()

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.documents import documents_bp
    from app.routes.folders import folders_bp
    from app.routes.search import search_bp
    from app.routes.share import share_bp
    from app.routes.analytics import analytics_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(folders_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(share_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)

    # Context processors and global template helpers
    @app.context_processor
    def inject_globals():
        current_user = None
        user_root_folders = []
        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])
            if current_user:
                g.current_user = current_user
                user_root_folders = Folder.query.filter_by(parent_id=None, is_deleted=False).order_by(Folder.name.asc()).all()

        return {
            'current_user': current_user,
            'root_folders': user_root_folders,
            'format_size': format_file_size,
            'time_ago': time_ago,
            'file_icon': get_file_icon,
            'category_color': get_category_color,
            'active_path': request.path
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def too_large_error(error):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Auto create tables on startup
    with app.app_context():
        db.create_all()

    return app
