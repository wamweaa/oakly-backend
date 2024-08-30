from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')

    def set_password(self, password):
        self.password = password  # You should hash the password in a real app

    def check_password(self, password):
        return self.password == password  # Check the hashed password in a real app

    def __repr__(self):
        return f'<User {self.name}>'

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each item
    name = db.Column(db.String(80), nullable=False)  # Name of the item, cannot be null
    
    # Establish a one-to-many relationship with the Product model
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

    # Foreign key to link each product to an item
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)

    def __repr__(self):
        return f'<Product {self.name}>'
