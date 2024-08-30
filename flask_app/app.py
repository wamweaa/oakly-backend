from functools import wraps
from flask import Flask, jsonify, request, g, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import traceback
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a real secret key

# Configuration for file uploads

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), UPLOAD_FOLDER)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    category = db.Column(db.String(100))
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


# Role-based access control decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None or g.user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# CRUD operations for Items
@app.route('/api/user', methods=['GET'])
def get_user():
    if g.user:
        return jsonify({
            'id': g.user.id,
            'name': g.user.name,
            'email': g.user.email,
            'phone': g.user.phone,
            'role': g.user.role
        })
    return jsonify({'error': 'Unauthorized'}), 401


@app.route('/api/user/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    if g.user and g.user.id == id:  # Check if the request is from the user being updated
        data = request.form
        if 'username' in data:
            user.name = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'contactNumber' in data:
            user.phone = data['contactNumber']
        if 'password' in data:
            user.set_password(data['password'])

        if 'avatar' in request.files:
            avatar = request.files['avatar']
            if avatar:
                filename = secure_filename(avatar.filename)
                avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                user.avatar = filename

        db.session.commit()

        return jsonify({'message': 'User updated successfully.'})

    return jsonify({'error': 'Unauthorized'}), 401


@app.route('/items', methods=['GET'])
def get_items():
    items = Item.query.all()
    return jsonify([{'id': item.id, 'name': item.name} for item in items])

@app.route('/items', methods=['POST'])
@admin_required
def create_item():
    data = request.json
    new_item = Item(name=data['name'])
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'id': new_item.id, 'name': new_item.name})

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify({'id': item.id, 'name': item.name})

@app.route('/items/<int:item_id>', methods=['PUT'])
@admin_required
def update_item(item_id):
    data = request.json
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    item.name = data.get('name', item.name)
    db.session.commit()
    return jsonify({'id': item.id, 'name': item.name})

@app.route('/items/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully'})

# CRUD operations for Products
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'image_url': product.image_url,
        'item_id': product.item_id
    } for product in products])

@app.route('/products', methods=['POST'])
@admin_required
def create_product():
    if 'image' not in request.files and 'image_url' not in request.form:
        return jsonify({'error': 'No image file or URL provided'}), 400

    image = request.files.get('image')
    if image and image.filename:
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        image_url = f'/uploads/{filename}'  # Ensure this path is correct
    else:
        image_url = request.form.get('image_url')

    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price', type=float)
    item_id = request.form.get('item_id', type=int)

    if not name or not price or not item_id:
        return jsonify({'error': 'Name, price, and item ID are required'}), 400

    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    new_product = Product(
        name=name,
        description=description,
        price=price,
        image_url=image_url,
        item_id=item_id
    )
    db.session.add(new_product)
    db.session.commit()

    return jsonify({
        'id': new_product.id,
        'name': new_product.name,
        'description': new_product.description,
        'price': new_product.price,
        'image_url': new_product.image_url,
        'item_id': new_product.item_id
    }), 201


@app.route('/products', methods=['GET'])
def get_products_by_category():
    category = request.args.get('category')
    if not category:
        return jsonify({'error': 'Category not provided'}), 400
    
    products = Product.query.filter_by(category=category).all()
    if not products:
        return jsonify({'error': 'No products found in this category'}), 404

    return jsonify([{
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'image_url': product.image_url
    } for product in products])


@app.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            product.image_url = f'/uploads/{filename}'  # Ensure this path is correct

    product.name = request.form.get('name', product.name)
    product.description = request.form.get('description', product.description)
    product.price = request.form.get('price', type=float, default=product.price)

    db.session.commit()
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'image_url': product.image_url,
        'item_id': product.item_id
    })

@app.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})

@app.route('/items/<int:item_id>/products', methods=['GET'])
def get_products_for_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    products = Product.query.filter_by(item_id=item.id).all()
    return jsonify([{
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'image_url': product.image_url
    } for product in products])

# User registration
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    name = data['name']
    email = data['email']
    phone = data.get('phone')
    password = data['password']
    role = data.get('role', 'user')

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message': 'User already exists!'}), 400

    new_user = User(name=name, email=email, phone=phone)
    new_user.set_password(password)
    new_user.role = role
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'})


# User login
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        token = jwt.encode({
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token, 'role': user.role})

    return jsonify({'error': 'Invalid credentials'}), 401

# Middleware to check authentication and load the current user
@app.before_request
def load_current_user():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]  # Remove 'Bearer ' prefix
        try:
            decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user = User.query.get(decoded['id'])
            if user:
                g.user = user
            else:
                return jsonify({'error': 'User not found'}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    else:
        g.user = None
from flask import request



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    print(f"Requested file: {filename}")  # For debugging
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/send-email', methods=['POST'])
def send_email():
    data = request.get_json()
    to_email = data['to']
    subject = data['subject']
    body = data['body']

    # Email configuration
    from_email = 'patokinya12@gmail.com'
    password = 'wayuamartha12'

    # Create the email content
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    # Send the email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        return jsonify({'message': 'Email sent successfully'}), 200
    except Exception as e:
        print('Failed to send email:', e)
        return jsonify({'message': 'Failed to send email'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)