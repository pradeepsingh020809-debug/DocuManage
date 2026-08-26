from flask import Blueprint, render_template, request, jsonify, g
from app.services import SearchService
from app.models import Tag, Folder
from app.utils.decorators import login_required

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
@login_required
def search_view():
    """Main search results page with full filter options."""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', 'all')
    tag_id = request.args.get('tag_id', type=int)
    folder_id = request.args.get('folder_id', type=int)
    is_starred = request.args.get('starred')
    is_starred_bool = True if is_starred == '1' else None

    results = []
    if query or category != 'all' or tag_id or folder_id or is_starred_bool:
        results = SearchService.search_documents(
            query_str=query,
            category=category,
            tag_id=tag_id,
            folder_id=folder_id,
            is_starred=is_starred_bool,
            current_user_id=g.current_user.id
        )

    all_tags = Tag.query.order_by(Tag.name.asc()).all()
    all_folders = Folder.query.filter_by(is_deleted=False).all()

    return render_template(
        'explorer/search.html',
        query=query,
        category=category,
        selected_tag=tag_id,
        selected_folder=folder_id,
        results=results,
        all_tags=all_tags,
        all_folders=all_folders
    )

@search_bp.route('/api/search')
@login_required
def search_api():
    """Instant search endpoint returning JSON for live navbar search."""
    query = request.args.get('q', '').strip()
    category = request.args.get('category')
    tag_id = request.args.get('tag_id', type=int)

    if not query and not category and not tag_id:
        return jsonify({'results': []})

    results = SearchService.search_documents(
        query_str=query,
        category=category,
        tag_id=tag_id,
        current_user_id=g.current_user.id,
        limit=10
    )

    return jsonify({'results': results, 'count': len(results)})
