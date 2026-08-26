from datetime import datetime, timezone

def format_file_size(size_bytes: int) -> str:
    """Formats bytes to human readable format (KB, MB, GB)."""
    if not size_bytes or size_bytes <= 0:
        return '0 B'
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    idx = 0
    size = float(size_bytes)
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1
    
    if idx == 0:
        return f"{int(size)} {units[idx]}"
    return f"{size:.1f} {units[idx]}"

def time_ago(dt: datetime) -> str:
    """Returns a relative humanized timestamp."""
    if not dt:
        return ""
    
    now = datetime.now(timezone.utc)
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 5:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    
    days = hours // 24
    if days < 7:
        return f"{days}d ago"
    if days < 30:
        weeks = days // 7
        return f"{weeks}w ago"
    if days < 365:
        months = days // 30
        return f"{months}mo ago"
    
    years = days // 365
    return f"{years}y ago"

def get_file_icon(ext: str, category: str = None) -> str:
    """Returns the Lucide icon name matching the file type."""
    ext = (ext or '').lower().lstrip('.')
    
    icon_map = {
        # PDF
        'pdf': 'file-text',
        # Documents
        'doc': 'file-text', 'docx': 'file-text', 'odt': 'file-text', 'rtf': 'file-text',
        # Spreadsheets
        'xls': 'sheet', 'xlsx': 'sheet', 'csv': 'sheet', 'tsv': 'sheet',
        # Presentations
        'ppt': 'presentation', 'pptx': 'presentation',
        # Images
        'png': 'image', 'jpg': 'image', 'jpeg': 'image', 'gif': 'image', 'svg': 'image', 'webp': 'image',
        # Code
        'py': 'code-xml', 'js': 'code-xml', 'ts': 'code-xml', 'html': 'code-xml', 'css': 'code-xml',
        'json': 'brackets', 'yaml': 'brackets', 'yml': 'brackets', 'sql': 'database', 'sh': 'terminal',
        # Text
        'txt': 'file-text', 'md': 'file-code', 'markdown': 'file-code', 'log': 'file-terminal',
        # Archives
        'zip': 'archive', 'tar': 'archive', 'gz': 'archive', '7z': 'archive', 'rar': 'archive',
        # Audio / Video
        'mp3': 'music', 'wav': 'music', 'mp4': 'video', 'webm': 'video'
    }
    
    if ext in icon_map:
        return icon_map[ext]
    
    cat_map = {
        'pdf': 'file-text',
        'document': 'file-text',
        'spreadsheet': 'sheet',
        'presentation': 'presentation',
        'image': 'image',
        'code': 'code-xml',
        'text': 'file-text',
        'archive': 'archive',
        'audio': 'music',
        'video': 'video'
    }
    
    return cat_map.get(category, 'file')

def get_category_color(category: str) -> str:
    """Returns CSS color or hex associated with category."""
    colors = {
        'pdf': '#ef4444',
        'document': '#3b82f6',
        'spreadsheet': '#10b981',
        'presentation': '#f59e0b',
        'image': '#ec4899',
        'code': '#8b5cf6',
        'text': '#64748b',
        'archive': '#6366f1',
        'audio': '#06b6d4',
        'video': '#f97316'
    }
    return colors.get(category, '#64748b')
