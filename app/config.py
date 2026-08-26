import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'docuvault-super-secret-key-change-in-production-2026')
    
    # SQLite Database
    INSTANCE_DIR = BASE_DIR / 'instance'
    INSTANCE_DIR.mkdir(exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f'sqlite:///{INSTANCE_DIR / "docuvault.db"}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage paths
    STORAGE_DIR = BASE_DIR / 'storage'
    UPLOAD_DIR = STORAGE_DIR / 'uploads'
    THUMBNAIL_DIR = STORAGE_DIR / 'thumbnails'
    VERSIONS_DIR = STORAGE_DIR / 'versions'
    
    # Max upload limit: 200 MB
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024
    
    # Allowed categories
    ALLOWED_EXTENSIONS = {
        'pdf': 'pdf',
        'doc': 'document', 'docx': 'document', 'odt': 'document', 'rtf': 'document',
        'xls': 'spreadsheet', 'xlsx': 'spreadsheet', 'csv': 'spreadsheet', 'tsv': 'spreadsheet',
        'ppt': 'presentation', 'pptx': 'presentation',
        'txt': 'text', 'md': 'text', 'markdown': 'text', 'log': 'text',
        'png': 'image', 'jpg': 'image', 'jpeg': 'image', 'gif': 'image', 'svg': 'image', 'webp': 'image', 'bmp': 'image',
        'py': 'code', 'js': 'code', 'html': 'code', 'css': 'code', 'json': 'code', 'yaml': 'code', 'yml': 'code',
        'sql': 'code', 'sh': 'code', 'java': 'code', 'cpp': 'code', 'c': 'code', 'xml': 'code', 'ts': 'code',
        'zip': 'archive', 'tar': 'archive', 'gz': 'archive', '7z': 'archive', 'rar': 'archive',
        'mp3': 'audio', 'wav': 'audio', 'ogg': 'audio',
        'mp4': 'video', 'webm': 'video', 'mov': 'video'
    }
    
    # Preview supported extensions
    PREVIEW_EXTENSIONS = {
        'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp',
        'txt', 'md', 'markdown', 'csv', 'tsv', 'json', 'yaml', 'yml',
        'py', 'js', 'html', 'css', 'sql', 'sh', 'xml', 'log', 'ts',
        'mp3', 'wav', 'ogg', 'mp4', 'webm'
    }
