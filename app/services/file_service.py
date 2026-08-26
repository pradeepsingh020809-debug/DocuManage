import os
import hashlib
import uuid
import zipfile
import io
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app
from app.config import Config

class FileService:
    @staticmethod
    def ensure_storage_dirs():
        """Ensure all required storage directories exist."""
        Config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        Config.THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
        Config.VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Calculate SHA-256 hash of a file for data integrity verification."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def save_upload(file_storage, user_id: int) -> tuple[str, str, Path, int]:
        """
        Saves an uploaded file safely to disk.
        Returns: (original_filename, stored_filename, absolute_path, file_size)
        """
        FileService.ensure_storage_dirs()
        original_name = secure_filename(file_storage.filename) or 'unnamed_file'
        extension = Path(original_name).suffix.lower()
        
        # Generate unique storage filename
        unique_token = uuid.uuid4().hex
        stored_name = f"{user_id}_{unique_token}{extension}"
        dest_path = Config.UPLOAD_DIR / stored_name
        
        file_storage.save(str(dest_path))
        file_size = os.path.getsize(dest_path)
        
        return original_name, stored_name, dest_path, file_size

    @staticmethod
    def save_version_file(file_storage, document_id: int, version_num: int) -> tuple[str, str, Path, int]:
        """
        Saves a new revision file to the versions directory.
        Returns: (original_filename, stored_filename, absolute_path, file_size)
        """
        FileService.ensure_storage_dirs()
        original_name = secure_filename(file_storage.filename) or f"doc_{document_id}_v{version_num}"
        extension = Path(original_name).suffix.lower()
        
        unique_token = uuid.uuid4().hex
        stored_name = f"doc{document_id}_v{version_num}_{unique_token}{extension}"
        dest_path = Config.VERSIONS_DIR / stored_name
        
        file_storage.save(str(dest_path))
        file_size = os.path.getsize(dest_path)
        
        return original_name, stored_name, dest_path, file_size

    @staticmethod
    def delete_physical_file(file_path_str: str):
        """Safely remove a file from disk if it exists."""
        if not file_path_str:
            return
        path = Path(file_path_str)
        if path.exists() and path.is_file():
            try:
                path.unlink()
            except Exception as e:
                print(f"Error removing physical file {path}: {e}")

    @staticmethod
    def create_zip_archive(documents: list) -> io.BytesIO:
        """
        Generates an in-memory ZIP file containing the specified list of Document objects.
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            used_names = set()
            for doc in documents:
                if not doc.file_path or not os.path.exists(doc.file_path):
                    continue
                name = doc.filename
                # Handle duplicate filenames inside the zip
                idx = 1
                while name in used_names:
                    stem = Path(doc.filename).stem
                    ext = Path(doc.filename).suffix
                    name = f"{stem}_{idx}{ext}"
                    idx += 1
                used_names.add(name)
                zf.write(doc.file_path, arcname=name)
        zip_buffer.seek(0)
        return zip_buffer
