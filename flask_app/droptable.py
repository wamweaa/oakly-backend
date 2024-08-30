from app import app
from models import db

def drop_all_tables():
    with app.app_context():
        db.reflect()  # Reflects the database schema into the models
        db.drop_all()  # Drops all the reflected tables
        print("All tables dropped successfully.")

if __name__ == '__main__':
    drop_all_tables()
