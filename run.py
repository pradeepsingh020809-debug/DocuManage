import os
from app import create_app
from app.models import db, User
from seed_data import seed

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            print("Detected empty database. Running automatic demo seeder...")
            seed()

    port = int(os.environ.get('PORT', 5000))
    print(f"\n========================================================")
    print(f">> DocuVault - Document Management System is running!")
    print(f"[*] Local Web Interface: http://127.0.0.1:{port}")
    print(f"[*] Demo Admin:   username='Pradeep', password='Pradeep123'")
    print(f"[*] Demo Manager: username='sarah',   password='sarah123'")
    print(f"========================================================\n")

    app.run(host='0.0.0.0', port=port, debug=True)
