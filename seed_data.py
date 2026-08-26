import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from app import create_app
from app.models import db, User, Folder, Document, DocumentVersion, Tag, DocumentShare, Comment, ActivityLog
from app.config import Config
from app.services import MetadataService, FileService
import pypdf

def generate_sample_pdf(file_path: Path, title: str, content: str):
    """Generate a clean test PDF with pypdf or minimal raw pdf stream."""
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    # Write blank pdf structure
    with open(file_path, "wb") as fp:
        writer.write(fp)

def seed():
    app = create_app()
    with app.app_context():
        FileService.ensure_storage_dirs()

        # Check if already seeded
        if User.query.filter_by(username='master').first():
            print("Database already contains master user. Skipping seed.")
            return

        print("Creating initial database tables...")
        db.create_all()

        # 1. Create Users
        print("Creating users...")
        master = User(
            username='master',
            email='master@docuvault.io',
            full_name='Master Administrator',
            role='admin',
            avatar_color='#6366f1'
        )
        master.set_password('naster123')

        db.session.add(master)
        db.session.commit()

        # 2. Create Tags
        print("Creating tags...")
        tags = {
            'confidential': Tag(name='confidential', color='#ef4444'),
            'financial': Tag(name='financial', color='#10b981'),
            'q3-report': Tag(name='q3-report', color='#3b82f6'),
            'architecture': Tag(name='architecture', color='#8b5cf6'),
            'guidelines': Tag(name='guidelines', color='#f59e0b'),
            'verified': Tag(name='verified', color='#06b6d4')
        }
        db.session.add_all(tags.values())
        db.session.commit()

        # 3. Create Folders
        print("Creating folder hierarchy...")
        f_hr = Folder(name='Company Policies & HR', description='Employee handbooks, benefits, and compliance', color='#6366f1', user_id=master.id)
        f_fin = Folder(name='Financial Audits 2026', description='Quarterly balance sheets, P&L statements, tax filings', color='#10b981', user_id=master.id)
        f_tech = Folder(name='Engineering & Architecture', description='System designs, API specs, and technical documentation', color='#8b5cf6', user_id=master.id)
        f_prod = Folder(name='Product Roadmaps', description='Feature backlogs, UI mockups, and customer feedback', color='#f59e0b', user_id=master.id)

        db.session.add_all([f_hr, f_fin, f_tech, f_prod])
        db.session.commit()

        # Subfolders
        f_tax = Folder(name='Q3 Tax Returns', description='Subfolder for Q3 records', color='#10b981', parent_id=f_fin.id, user_id=master.id)
        f_api = Folder(name='REST API Specs', description='API endpoints and schema definitions', color='#8b5cf6', parent_id=f_tech.id, user_id=master.id)
        db.session.add_all([f_tax, f_api])
        db.session.commit()

        # 4. Generate & Save Sample Documents with real disk files
        print("Creating documents and versions...")
        
        sample_files_data = [
            {
                'title': 'Enterprise System Architecture & Microservices Specification',
                'filename': 'system_architecture_spec.md',
                'category': 'text',
                'folder': f_tech,
                'user': admin,
                'tags': [tags['architecture'], tags['verified']],
                'is_starred': True,
                'content': """# Enterprise System Architecture (2026 Revision)

## 1. Overview
DocuVault is structured as a resilient, distributed document storage architecture supporting:
- Multi-tier role-based access control (RBAC).
- Instant full-text document content indexing and search.
- Cryptographic SHA-256 integrity hashing on all revisions.
- In-browser dynamic rendering of PDFs, Markdown, CSVs, and syntax-highlighted code.

## 2. Component Architecture
- **Web API Layer**: Flask 3.1 REST endpoints and Jinja2 reactive templates.
- **Data Layer**: Relational SQLite database with automated foreign key constraints.
- **Storage Layer**: Partitioned disk storage with isolated revision version directories.
- **Search Engine**: Tokenized full-text lexical ranking and snippet generator.

## 3. High-Throughput Processing Pipeline
```python
def process_document(file_stream, user_id):
    sha256_hash = calculate_hash(file_stream)
    metadata = extract_content_text(file_stream)
    return Document(checksum=sha256_hash, **metadata)
```
"""
            },
            {
                'title': 'Q3 2026 Global Financial Summary & Projections',
                'filename': 'financial_summary_q3.csv',
                'category': 'spreadsheet',
                'folder': f_fin,
                'user': master,
                'tags': [tags['financial'], tags['q3-report'], tags['confidential']],
                'is_starred': True,
                'content': """Quarter,Region,Revenue (USD),Operating Expenses,Net Profit,YoY Growth
Q1 2026,North America,12500000,7800000,4700000,+18.4%
Q1 2026,Europe (EMEA),8900000,5400000,3500000,+14.2%
Q1 2026,Asia-Pacific,6400000,3800000,2600000,+22.1%
Q2 2026,North America,14200000,8100000,6100000,+21.0%
Q2 2026,Europe (EMEA),9800000,5900000,3900000,+16.5%
Q2 2026,Asia-Pacific,7500000,4200000,3300000,+26.8%
Q3 2026,North America,16800000,8900000,7900000,+24.3%
Q3 2026,Europe (EMEA),11200000,6400000,4800000,+19.1%
Q3 2026,Asia-Pacific,8900000,4700000,4200000,+31.2%
"""
            },
            {
                'title': 'Employee Code of Conduct & Security Handbook',
                'filename': 'employee_handbook_2026.txt',
                'category': 'text',
                'folder': f_hr,
                'user': master,
                'tags': [tags['guidelines'], tags['verified']],
                'is_starred': False,
                'content': """DOCUVAULT CORP - EMPLOYEE CODE OF CONDUCT (2026)

Section 1: Information Security & Data Governance
- All company assets, confidential documents, and source repositories must be stored in approved encrypted repositories.
- Document links shared externally must always specify an expiration timeline not exceeding 30 calendar days.
- Access to sensitive financial records is strictly governed by Manager and Admin privileges.

Section 2: Version Control Protocols
- Any revision modifying customer-facing agreements must include a detailed change summary in the version metadata log.
- Do not overwrite active revisions without archiving prior drafts.
"""
            },
            {
                'title': 'Core Document Indexing & Storage Engine',
                'filename': 'storage_service.py',
                'category': 'code',
                'folder': f_api,
                'user': master,
                'tags': [tags['architecture']],
                'is_starred': False,
                'content': """# Core Storage & Hashing Engine
import os
import hashlib
from pathlib import Path

class StorageService:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def calculate_sha256(self, file_path: Path) -> str:
        \"\"\"Compute SHA-256 hash for document integrity.\"\"\"
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def verify_integrity(self, file_path: Path, expected_hash: str) -> bool:
        return self.calculate_sha256(file_path) == expected_hash
"""
            },
            {
                'title': 'API Gateway Configuration & Microservices Map',
                'filename': 'api_gateway_config.json',
                'category': 'code',
                'folder': f_api,
                'user': master,
                'tags': [tags['architecture']],
                'is_starred': False,
                'content': """{
  "environment": "production-cluster-2026",
  "version": "3.4.0",
  "routes": [
    { "path": "/api/v1/documents", "target": "document-service:5000", "rate_limit": 1000 },
    { "path": "/api/v1/search", "target": "search-index-service:5001", "rate_limit": 500 },
    { "path": "/api/v1/auth", "target": "identity-service:5002", "rate_limit": 200 }
  ],
  "security": {
    "enable_cors": true,
    "ssl_enforced": true,
    "jwt_issuer": "https://auth.docuvault.io"
  }
}"""
            },
            {
                'title': 'Official Company Vector Brand Logo',
                'filename': 'docuvault_logo_vector.svg',
                'category': 'image',
                'folder': None, # Root
                'user': master,
                'tags': [tags['guidelines']],
                'is_starred': True,
                'content': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120" width="400" height="120">
  <defs>
    <linearGradient id="brandGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6366f1"/>
      <stop offset="100%" stop-color="#a855f7"/>
    </linearGradient>
  </defs>
  <rect x="20" y="20" width="80" height="80" rx="20" fill="url(#brandGrad)"/>
  <path d="M40 45 L60 35 L80 45 L60 55 Z" fill="#ffffff" opacity="0.9"/>
  <path d="M40 60 L60 70 L80 60" fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round"/>
  <path d="M40 75 L60 85 L80 75" fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round"/>
  <text x="120" y="72" font-family="Plus Jakarta Sans, sans-serif" font-size="42" font-weight="800" fill="#6366f1">Docu<tspan fill="#a855f7">Vault</tspan></text>
</svg>"""
            }
        ]

        total_storage = 0

        for item in sample_files_data:
            filename = item['filename']
            file_path = Config.UPLOAD_DIR / f"{master.id}_{filename}"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(item['content'])

            file_size = os.path.getsize(file_path)
            total_storage += file_size
            sha256_hash = FileService.calculate_sha256(file_path)
            meta = MetadataService.extract_document_metadata(file_path, filename)

            doc = Document(
                title=item['title'],
                description=f"Standard enterprise asset: {item['title']}",
                filename=filename,
                stored_filename=file_path.name,
                file_path=str(file_path),
                file_size=file_size,
                mime_type=meta['mime_type'],
                file_extension=meta['file_extension'],
                category=meta['category'],
                checksum_sha256=sha256_hash,
                folder_id=item['folder'].id if item['folder'] else None,
                user_id=item['user'].id,
                is_starred=item.get('is_starred', False),
                current_version=1,
                extracted_text=meta['extracted_text'],
                page_count=meta['page_count'],
                word_count=meta['word_count'],
                dimensions=meta['dimensions']
            )
            for t in item['tags']:
                doc.tags.append(t)

            db.session.add(doc)
            db.session.flush()

            # Version 1 record
            v1 = DocumentVersion(
                document_id=doc.id,
                version_number=1,
                filename=filename,
                stored_filename=file_path.name,
                file_path=str(file_path),
                file_size=file_size,
                checksum_sha256=sha256_hash,
                change_summary='Initial document release',
                uploaded_by_id=item['user'].id
            )
            db.session.add(v1)

            # If it's the financial summary, create a Version 2 to showcase version history!
            if 'financial_summary' in filename:
                v2_filename = f"v2_{filename}"
                v2_path = Config.VERSIONS_DIR / f"doc{doc.id}_v2_{filename}"
                v2_content = item['content'] + "Q4 2026 (Forecast),Global Aggregate,45000000,24000000,21000000,+28.5%\n"
                with open(v2_path, 'w', encoding='utf-8') as f:
                    f.write(v2_content)
                v2_size = os.path.getsize(v2_path)
                v2_hash = FileService.calculate_sha256(v2_path)

                v2 = DocumentVersion(
                    document_id=doc.id,
                    version_number=2,
                    filename=filename,
                    stored_filename=v2_path.name,
                    file_path=str(v2_path),
                    file_size=v2_size,
                    checksum_sha256=v2_hash,
                    change_summary='Appended Q4 2026 Global Aggregate Forecast projections',
                    uploaded_by_id=master.id
                )
                db.session.add(v2)
                doc.current_version = 2
                doc.file_path = str(v2_path)
                doc.file_size = v2_size
                doc.checksum_sha256 = v2_hash
                doc.page_count = 10

            # Add sample comment
            comment = Comment(
                document_id=doc.id,
                user_id=master.id,
                content=f"Document '{doc.title}' has been reviewed and verified for integrity."
            )
            db.session.add(comment)

            # Add sample activity
            act = ActivityLog(
                user_id=item['user'].id,
                action='UPLOAD',
                document_id=doc.id,
                folder_id=doc.folder_id,
                details=f"Uploaded initial release of {filename}"
            )
            db.session.add(act)

        # 5. Create a sample public share link for demo
        first_doc = Document.query.first()
        if first_doc:
            share = DocumentShare(
                document_id=first_doc.id,
                created_by_id=master.id,
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                allow_download=True,
                access_count=5
            )
            db.session.add(share)

        master.storage_used = total_storage
        db.session.commit()

        print("Data seeding completed successfully!")
        print("Master Credentials:")
        print("  Admin: username='master', password='naster123'")

if __name__ == '__main__':
    seed()
