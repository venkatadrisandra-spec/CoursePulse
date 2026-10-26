from app import create_app, db, seed_default_data

app = create_app()
with app.app_context():
    db.create_all()
    seed_default_data(app)
    print("Database tables are ready and demo course data has been loaded.")
