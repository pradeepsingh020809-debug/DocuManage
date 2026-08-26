import unittest
import io
from app import create_app
from app.models import db, User, Document, Folder, Tag

class DocuVaultTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def login(self, username='master', password='naster123'):
        return self.client.post('/auth/login', data={
            'identifier': username,
            'password': password
        }, follow_redirects=True)

    def test_login_and_dashboard(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'master', response.data)
        self.assertIn(b'Storage Distribution', response.data)

    def test_explorer_and_files(self):
        self.login()
        response = self.client.get('/explorer')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Company Policies', response.data)

    def test_search_api(self):
        self.login()
        response = self.client.get('/api/search?q=architecture')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(len(data['results']) > 0)

    def test_preview_data_endpoint(self):
        self.login()
        with self.app.app_context():
            doc = Document.query.filter(Document.filename.like('%.md')).first()
            self.assertIsNotNone(doc)
            doc_id = doc.id
        
        response = self.client.get(f'/documents/{doc_id}/preview-data')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['id'], doc_id)
        self.assertIn('rendered_html', data)

    def test_document_details_page(self):
        self.login()
        with self.app.app_context():
            doc = Document.query.first()
            doc_id = doc.id
        
        response = self.client.get(f'/documents/{doc_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'File Properties', response.data)
        self.assertIn(b'Version History', response.data)

    def test_create_folder_and_upload(self):
        self.login()
        # Create folder
        res_folder = self.client.post('/folder/create', data={
            'name': 'Test Integration Folder',
            'description': 'Integration testing folder'
        }, follow_redirects=True)
        self.assertEqual(res_folder.status_code, 200)

        # Get folder id
        with self.app.app_context():
            folder = Folder.query.filter_by(name='Test Integration Folder').first()
            self.assertIsNotNone(folder)
            folder_id = folder.id

        # Upload a file
        test_file = (io.BytesIO(b"Hello World integration test content for DMS"), "integration_test.txt")
        res_upload = self.client.post('/documents/upload', data={
            'files': [test_file],
            'folder_id': str(folder_id),
            'tags': 'test, automated'
        }, follow_redirects=True)
        self.assertEqual(res_upload.status_code, 200)

        with self.app.app_context():
            uploaded_doc = Document.query.filter_by(filename='integration_test.txt').first()
            self.assertIsNotNone(uploaded_doc)
            self.assertEqual(uploaded_doc.folder_id, folder_id)
            self.assertEqual(uploaded_doc.current_version, 1)

if __name__ == '__main__':
    unittest.main()
