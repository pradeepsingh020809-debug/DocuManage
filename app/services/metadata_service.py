import os
import mimetypes
from pathlib import Path
from PIL import Image
import pypdf
from app.config import Config

class MetadataService:
    @staticmethod
    def get_file_category(extension: str) -> str:
        """Categorize file based on extension."""
        ext = extension.lower().lstrip('.')
        return Config.ALLOWED_EXTENSIONS.get(ext, 'other')

    @staticmethod
    def detect_mime_type(file_path: Path, filename: str) -> str:
        """Detect MIME type from file content/extension."""
        mime, _ = mimetypes.guess_type(filename)
        if mime:
            return mime
        ext = Path(filename).suffix.lower()
        mapping = {
            '.md': 'text/markdown',
            '.py': 'text/x-python',
            '.js': 'text/javascript',
            '.ts': 'text/typescript',
            '.json': 'application/json',
            '.yaml': 'text/yaml',
            '.yml': 'text/yaml',
            '.sql': 'application/sql',
            '.csv': 'text/csv',
            '.tsv': 'text/tab-separated-values',
            '.log': 'text/plain'
        }
        return mapping.get(ext, 'application/octet-stream')

    @staticmethod
    def extract_document_metadata(file_path: Path, filename: str) -> dict:
        """
        Extracts searchable text, page count, word count, dimensions, etc.
        """
        ext = Path(filename).suffix.lower().lstrip('.')
        category = MetadataService.get_file_category(ext)
        mime_type = MetadataService.detect_mime_type(file_path, filename)
        
        extracted_text = ""
        page_count = None
        word_count = None
        dimensions = None

        try:
            # 1. PDF Extraction
            if ext == 'pdf':
                try:
                    reader = pypdf.PdfReader(str(file_path))
                    page_count = len(reader.pages)
                    text_parts = []
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            text_parts.append(t)
                    extracted_text = "\n".join(text_parts)
                    word_count = len(extracted_text.split()) if extracted_text else 0
                except Exception as e:
                    print(f"PDF extraction error for {filename}: {e}")

            # 2. Text & Code Extraction (txt, md, py, js, html, css, json, csv, etc.)
            elif category in ['text', 'code', 'spreadsheet'] or ext in ['txt', 'md', 'csv', 'json', 'py', 'js', 'html', 'css', 'sql', 'log', 'yaml', 'yml']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        extracted_text = f.read(500000) # Read up to ~500KB of text
                    word_count = len(extracted_text.split()) if extracted_text else 0
                    if ext in ['csv', 'tsv']:
                        page_count = extracted_text.count('\n') + 1 # row count
                except Exception as e:
                    print(f"Text extraction error for {filename}: {e}")

            # 3. Image Metadata (dimensions, thumbnail)
            elif category == 'image':
                try:
                    with Image.open(str(file_path)) as img:
                        dimensions = f"{img.width}x{img.height}"
                        # Generate thumbnail if feasible
                        thumb_dir = Config.THUMBNAIL_DIR
                        thumb_dir.mkdir(parents=True, exist_ok=True)
                        thumb_name = f"thumb_{file_path.stem}.webp"
                        thumb_path = thumb_dir / thumb_name
                        
                        img.thumbnail((300, 300))
                        img.convert('RGB').save(str(thumb_path), 'WEBP', quality=85)
                except Exception as e:
                    print(f"Image processing error for {filename}: {e}")

        except Exception as e:
            print(f"General metadata extraction error for {filename}: {e}")

        return {
            'mime_type': mime_type,
            'category': category,
            'file_extension': ext,
            'extracted_text': extracted_text[:100000] if extracted_text else None, # limit DB storage
            'page_count': page_count,
            'word_count': word_count,
            'dimensions': dimensions
        }
