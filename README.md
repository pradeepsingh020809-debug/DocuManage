# 📂 DocuVault - Enterprise Document Management System (DMS)

**DocuVault** is a full-featured, secure, and modern Document Management System web application built in **Python (Flask)** with a responsive **Glassmorphism UI**, full-text search, in-browser multi-format previewing, document version control, and access control.

---

## ✨ Key Features

1. **📁 Hierarchical Document & Folder Management**:
   - Nested directory structures with fast breadcrumb navigation.
   - Dual view modes: **Visual Card Grid** & **Rich Tabular List View**.
   - Custom folder accent colors, description, and fast tree sidebar.

2. **👁️ In-Browser Multi-Format Document Previewer**:
   - **PDFs**: Embedded viewer.
   - **Images**: PNG, JPG, GIF, WebP, SVG with responsive preview.
   - **Markdown**: Formatted HTML rendering with tables & code styling.
   - **Spreadsheets (CSV/TSV)**: Interactive tabular rendering with sticky headers.
   - **Code & Text**: Python, JavaScript, HTML, CSS, SQL, JSON, YAML with syntax formatting.

3. **🔄 Document Version Control & History**:
   - Multi-revision tracking (v1, v2, v3...) without file loss.
   - Change summaries and author attribution per revision.
   - 1-click revision rollback and previous version downloads.

4. **🔍 Instant Full-Text & Multi-Criteria Search**:
   - Live debounced navbar search (`/` keyboard shortcut).
   - Search across document titles, descriptions, tags, and document text content.
   - Filter by file category (PDFs, Images, Spreadsheets, Documents, Code, Archives), upload date, and folder.

5. **🔒 Security, Auth & RBAC**:
   - User authentication with hashed passwords (PBKDF2/SHA256).
   - Roles: `Admin`, `Manager`, `Editor`, `Viewer`.
   - Comprehensive audit trail logging every view, download, edit, version upload, and deletion.

6. **🔗 Secure Document Sharing**:
   - Public and password-protected external shareable links.
   - Configurable expiration limits (24 hours, 7 days, 30 days, or permanent).
   - Access counters and one-click link revocation.

7. **🗑️ Recycle Bin (Trash) & Batch Operations**:
   - Soft deletion with 1-click restore or permanent file wipe.
   - Batch actions: Multi-select documents to **Delete**, **Move to Folder**, or **Download as ZIP**.

8. **📊 Storage & Analytics Dashboard**:
   - Storage quota bar and real-time usage metrics.
   - Category distribution charts (PDFs, Images, Spreadsheets, Code, Archives).
   - Recent uploads grid and global activity timeline.

9. **🎨 Premium Modern Design**:
   - Deep slate and indigo glassmorphic design system.
   - Dark / Light mode toggle saved in user preferences.
   - Floating toast notification system.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Demo Data & Start the Server
```bash
python run.py
```

### 3. Open in Browser
Visit **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### 🔑 Demo Accounts:
| Role | Username | Password |
|---|---|---|
| **Admin** | `Pradeep` | `Pradeep123` |
| **Manager** | `sarah` | `sarah123` |

*(You can also use the "Fill Demo Admin Credentials" button directly on the login page!)*

---

## 🛠️ Project Structure

```
DocumentManagementSystem/
├── app/
│   ├── config.py                 # Application configuration & storage paths
│   ├── models/                   # SQLAlchemy database models
│   │   ├── user.py               # User & authentication
│   │   ├── folder.py             # Folder hierarchy
│   │   ├── document.py           # Document, DocumentVersion, Tag, Share
│   │   └── audit.py              # ActivityLog & Comments
│   ├── routes/                   # Flask Blueprints
│   │   ├── auth.py               # Login, Register, Profile
│   │   ├── documents.py          # Upload, Details, Preview, Versions, Download
│   │   ├── folders.py            # Explorer, Folders, Trash, Starred
│   │   ├── search.py             # Search engine & instant API
│   │   ├── share.py              # Public / password-protected share routes
│   │   ├── analytics.py          # Dashboard storage analytics
│   │   └── api.py                # Batch operations (ZIP download, Move, Delete)
│   ├── services/
│   │   ├── file_service.py       # Storage, SHA-256 integrity, ZIP bundling
│   │   ├── metadata_service.py   # PDF text extraction, image dimensions, MIME
│   │   └── search_service.py     # Full-text ranking & snippet generator
│   ├── static/
│   │   ├── css/                  # Design system, glassmorphism, preview CSS
│   │   └── js/                   # Uploader, explorer, preview, theme, search JS
│   └── templates/                # Jinja2 HTML templates
├── storage/                      # Uploaded files and versioned files
├── run.py                        # Server runner
├── seed_data.py                  # Demo database seeder
└── requirements.txt              # Dependencies
```
