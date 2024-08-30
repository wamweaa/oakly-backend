import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Create the Flask app and configure it
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define models
class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    products = db.relationship('Product', backref='item', lazy=True)

    def __repr__(self):
        return f'<Item {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(400), nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)

    def __repr__(self):
        return f'<Product {self.name}>'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.name}>'
def add_sample_data():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Define sample items
        sample_items = [
            Item(name="Chair"),
            Item(name="Table"),
            Item(name="Lamp"),
            Item(name="Sofa"),
            Item(name="Bed"),
            Item(name="Desk"),
            Item(name="Bookshelf"),
            Item(name="Cabinet"),
        ]

        # Add items to the session
        db.session.add_all(sample_items)
        db.session.commit()
        
        # Retrieve items from the database for product association
        chair = Item.query.filter_by(name="Chair").first()
        table = Item.query.filter_by(name="Table").first()
        lamp = Item.query.filter_by(name="Lamp").first()
        sofa = Item.query.filter_by(name="Sofa").first()
        bed = Item.query.filter_by(name="Bed").first()
        desk = Item.query.filter_by(name="Desk").first()
        bookshelf = Item.query.filter_by(name="Bookshelf").first()
        cabinet = Item.query.filter_by(name="Cabinet").first()

        # Define sample products for each item
        sample_products = [
            Product(name="Dining Chair", description="A comfortable wooden dining chair.", price=49.99, image_url="uploads/dining_chair.jpg", item_id=chair.id),
            Product(name="Office Chair", description="Ergonomic office chair with lumbar support.", price=129.99, image_url="uploads/office_chair.jpg", item_id=chair.id),
            Product(name="Coffee Table", description="Modern glass coffee table.", price=79.99, image_url="uploads/coffee_table.jpg", item_id=table.id),
            Product(name="Desk Lamp", description="LED desk lamp with adjustable brightness.", price=29.99, image_url="uploads/desk_lamp.jpg", item_id=lamp.id),
            Product(name="Leather Sofa", description="Luxury leather sofa with reclining feature.", price=799.99, image_url="uploads/leather_sofa.jpg", item_id=sofa.id),
            Product(name="Queen Bed", description="Queen-sized bed with memory foam mattress.", price=599.99, image_url="uploads/queen_bed.jpg", item_id=bed.id),
            Product(name="Wooden Desk", description="Solid wooden desk with drawers.", price=229.99, image_url="uploads/wooden_desk.jpg", item_id=desk.id),
            Product(name="Bookshelf", description="Tall wooden bookshelf with adjustable shelves.", price=159.99, image_url="uploads/bookshelf.jpg", item_id=bookshelf.id),
            Product(name="Cabinet", description="Storage cabinet with multiple compartments.", price=119.99, image_url="uploads/cabinet.jpg", item_id=cabinet.id),
        ]

        # Add products to the session
        db.session.add_all(sample_products)
        db.session.commit()
        
        # Define sample users
        sample_users = [
            User(name="Admin User", email="admin@example.com", phone="123-456-7890", role="admin"),
            User(name="Regular User", email="user@example.com", phone="098-765-4321"),
        ]

        # Set passwords for sample users
        for user in sample_users:
            user.set_password("password123")

        # Add users to the session
        db.session.add_all(sample_users)
        db.session.commit()

        print("Sample data added successfully.")

if __name__ == '__main__':
    add_sample_data()
