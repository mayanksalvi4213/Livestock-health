from app import app, db
import os

def init_db():
    """Initialize the database by creating all tables"""
    with app.app_context():
        print("Creating database tables...")
        # Create database file directory if it doesn't exist
        db_path = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"Database file will be created at: {db_file}")
        
        if db_path and not os.path.exists(db_path):
            os.makedirs(db_path)
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 