"""
Part 4: REST API with Flask
===========================
Build a JSON API for database operations (used by frontend apps, mobile apps, etc.)

What You'll Learn:
- REST API concepts (GET, POST, PUT, DELETE)
- JSON responses with jsonify
- API error handling
- Status codes
- Testing APIs with curl or Postman

Prerequisites: Complete part-3 (SQLAlchemy)
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # ADD THIS IMPORT
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # ADD THIS LINE - enables CORS for all routes

# Database setup with instance folder
instance_path = os.path.join(os.path.dirname(__file__), 'instance')
os.makedirs(instance_path, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{instance_path}/api_demo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# =============================================================================
# MODELS
# =============================================================================

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    city = db.Column(db.String(100))
    books = db.relationship('Book', backref='author_ref', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'bio': self.bio,
            'city': self.city,
            'books_count': len(self.books) if self.books else 0
        }


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id', ondelete='CASCADE'), nullable=False)
    year = db.Column(db.Integer)
    isbn = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        author = Author.query.get(self.author_id)
        return {
            'id': self.id,
            'title': self.title,
            'author_id': self.author_id,
            'author_name': author.name if author else 'Unknown Author',
            'year': self.year,
            'isbn': self.isbn,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# AUTHOR API ROUTES
# =============================================================================

# GET /api/authors - Get all authors
@app.route('/api/authors', methods=['GET'])
def get_authors():
    authors = Author.query.all()
    return jsonify({
        'success': True,
        'count': len(authors),
        'authors': [author.to_dict() for author in authors]
    })


# GET /api/authors/<id> - Get single author with books
@app.route('/api/authors/<int:id>', methods=['GET'])
def get_author(id):
    author = Author.query.get(id)
    
    if not author:
        return jsonify({
            'success': False,
            'error': 'Author not found'
        }), 404
    
    author_data = author.to_dict()
    author_data['books'] = [book.to_dict() for book in author.books]
    
    return jsonify({
        'success': True,
        'author': author_data
    })


# POST /api/authors - Create new author
@app.route('/api/authors', methods=['POST'])
def create_author():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    if not data.get('name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    
    new_author = Author(
        name=data['name'],
        bio=data.get('bio'),
        city=data.get('city')
    )
    
    db.session.add(new_author)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Author created successfully',
        'author': new_author.to_dict()
    }), 201


# PUT /api/authors/<id> - Update author
@app.route('/api/authors/<int:id>', methods=['PUT'])
def update_author(id):
    author = Author.query.get(id)
    
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    if 'name' in data:
        author.name = data['name']
    if 'bio' in data:
        author.bio = data['bio']
    if 'city' in data:
        author.city = data['city']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Author updated successfully',
        'author': author.to_dict()
    })


# DELETE /api/authors/<id> - Delete author
@app.route('/api/authors/<int:id>', methods=['DELETE'])
def delete_author(id):
    author = Author.query.get(id)
    
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    
    # Since we have ondelete='CASCADE', books will be automatically deleted
    db.session.delete(author)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Author and associated books deleted successfully'
    })


# =============================================================================
# BOOK API ROUTES
# =============================================================================

# GET /api/books - Get all books with pagination and sorting
@app.route('/api/books', methods=['GET'])
def get_books():
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort_by = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')
    
    # Validate sort field
    allowed_sort_fields = ['id', 'title', 'year', 'created_at']
    if sort_by not in allowed_sort_fields:
        sort_by = 'id'
    
    # Apply sorting
    if sort_by == 'title':
        query = Book.query.order_by(Book.title.asc() if order == 'asc' else Book.title.desc())
    elif sort_by == 'year':
        query = Book.query.order_by(Book.year.asc() if order == 'asc' else Book.year.desc())
    elif sort_by == 'created_at':
        query = Book.query.order_by(Book.created_at.asc() if order == 'asc' else Book.created_at.desc())
    else:
        query = Book.query.order_by(Book.id.asc() if order == 'asc' else Book.id.desc())
    
    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items
    
    return jsonify({
        'success': True,
        'count': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'books': [book.to_dict() for book in books]
    })


# GET /api/books/<id> - Get single book
@app.route('/api/books/<int:id>', methods=['GET'])
def get_book(id):
    book = Book.query.get(id)
    
    if not book:
        return jsonify({
            'success': False,
            'error': 'Book not found'
        }), 404
    
    return jsonify({
        'success': True,
        'book': book.to_dict()
    })


# POST /api/books - Create new book
@app.route('/api/books', methods=['POST'])
def create_book():
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    if not data.get('title') or not data.get('author_id'):
        return jsonify({'success': False, 'error': 'Title and author_id are required'}), 400

    # Check if author exists
    author = Author.query.get(data['author_id'])
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 400

    # Check for duplicate ISBN
    if data.get('isbn'):
        existing = Book.query.filter_by(isbn=data['isbn']).first()
        if existing:
            return jsonify({'success': False, 'error': 'ISBN already exists'}), 400

    # Create book
    new_book = Book(
        title=data['title'],
        author_id=data['author_id'],
        year=data.get('year'),
        isbn=data.get('isbn')
    )

    db.session.add(new_book)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Book created successfully',
        'book': new_book.to_dict()
    }), 201


# PUT /api/books/<id> - Update book
@app.route('/api/books/<int:id>', methods=['PUT'])
def update_book(id):
    book = Book.query.get(id)

    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    # Update fields if provided
    if 'title' in data:
        book.title = data['title']
    if 'author_id' in data:
        # Check if author exists
        author = Author.query.get(data['author_id'])
        if not author:
            return jsonify({'success': False, 'error': 'Author not found'}), 400
        book.author_id = data['author_id']
    if 'year' in data:
        book.year = data['year']
    if 'isbn' in data:
        book.isbn = data['isbn']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Book updated successfully',
        'book': book.to_dict()
    })


# DELETE /api/books/<id> - Delete book
@app.route('/api/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get(id)
    
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    
    db.session.delete(book)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Book deleted successfully'
    })


# =============================================================================
# ADDITIONAL LEARNING ENDPOINTS (Simple pagination and sorting)
# =============================================================================

# GET /api/books-with-pagination - Simple pagination only (for learning)
@app.route('/api/books-with-pagination', methods=['GET'])
def get_books_paginated():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    
    pagination = Book.query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items
    
    return jsonify({
        'success': True,
        'count': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'books': [book.to_dict() for book in books]
    })


# GET /api/books-with-sorting - Simple sorting only (for learning)
@app.route('/api/books-with-sorting', methods=['GET'])
def get_books_sorted():
    sort_by = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')
    
    if sort_by == 'title':
        query = Book.query.order_by(Book.title.asc() if order == 'asc' else Book.title.desc())
    elif sort_by == 'year':
        query = Book.query.order_by(Book.year.asc() if order == 'asc' else Book.year.desc())
    elif sort_by == 'created_at':
        query = Book.query.order_by(Book.created_at.asc() if order == 'asc' else Book.created_at.desc())
    else:
        query = Book.query.order_by(Book.id.asc() if order == 'asc' else Book.id.desc())
    
    books = query.all()
    
    return jsonify({
        'success': True,
        'count': len(books),
        'sort_by': sort_by,
        'order': order,
        'books': [book.to_dict() for book in books]
    })

# GET /api/books/search - Search books by title and/or author name
@app.route('/api/books/search', methods=['GET'])
def search_books():
    q = request.args.get('q', '').strip()
    author = request.args.get('author', '').strip()

    query = Book.query.join(Author)

    if q:
        query = query.filter(Book.title.ilike(f"%{q}%"))

    if author:
        query = query.filter(Author.name.ilike(f"%{author}%"))

    books = query.all()

    return jsonify({
        'success': True,
        'count': len(books),
        'books': [book.to_dict() for book in books]
    }), 200

# =============================================================================
# WEB PAGES
# =============================================================================

@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>Part 4 - REST API Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }
            h1 { color: #e94560; }
            h2 { color: #0fcea1; margin-top: 30px; }
            .endpoint { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #e94560; }
            .author-endpoint { border-left-color: #0fcea1; }
            .method { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; margin-right: 10px; }
            .get { background: #27ae60; }
            .post { background: #f39c12; }
            .put { background: #3498db; }
            .delete { background: #e74c3c; }
            code { background: #0f3460; padding: 2px 6px; border-radius: 3px; }
            pre { background: #0f3460; padding: 15px; border-radius: 8px; overflow-x: auto; }
            a { color: #e94560; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .note { background: #2c3e50; padding: 10px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>📚 Book Management REST API</h1>
        <div class="note">
            <strong>✅ All Endpoints Implemented:</strong>
            <ul>
                <li>Author CRUD operations</li>
                <li>Book CRUD operations</li>
                <li>Pagination and Sorting</li>
                <li>Book-Author relationships</li>
            </ul>
        </div>

        <h2>🎨 Frontend</h2>
        <div class="endpoint">
            <a href="/frontend" target="_blank" style="font-size: 1.2em;">Open Modern Frontend →</a>
        </div>

        <h2>👥 Author API Endpoints:</h2>

        <div class="endpoint author-endpoint">
            <span class="method get">GET</span>
            <code>/api/authors</code> - Get all authors
            <br><a href="/api/authors" target="_blank">Try it →</a>
        </div>

        <div class="endpoint author-endpoint">
            <span class="method get">GET</span>
            <code>/api/authors/&lt;id&gt;</code> - Get single author with books
            <br><a href="/api/authors/1" target="_blank">Try it (ID: 1) →</a>
        </div>

        <div class="endpoint author-endpoint">
            <span class="method post">POST</span>
            <code>/api/authors</code> - Create new author
        </div>

        <div class="endpoint author-endpoint">
            <span class="method put">PUT</span>
            <code>/api/authors/&lt;id&gt;</code> - Update author
        </div>

        <div class="endpoint author-endpoint">
            <span class="method delete">DELETE</span>
            <code>/api/authors/&lt;id&gt;</code> - Delete author
        </div>

        <h2>📚 Book API Endpoints:</h2>

        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/books</code> - Get all books (with pagination & sorting)
            <br>Examples: 
            <ul>
                <li><a href="/api/books?page=1&per_page=5" target="_blank">/api/books?page=1&per_page=5</a></li>
                <li><a href="/api/books?sort=title&order=desc" target="_blank">/api/books?sort=title&order=desc</a></li>
                <li><a href="/api/books?page=1&per_page=3&sort=year&order=asc" target="_blank">/api/books?page=1&per_page=3&sort=year&order=asc</a></li>
            </ul>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/books/&lt;id&gt;</code> - Get single book
            <br><a href="/api/books/1" target="_blank">Try it (ID: 1) →</a>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span>
            <code>/api/books</code> - Create new book
        </div>

        <div class="endpoint">
            <span class="method put">PUT</span>
            <code>/api/books/&lt;id&gt;</code> - Update book
        </div>

        <div class="endpoint">
            <span class="method delete">DELETE</span>
            <code>/api/books/&lt;id&gt;</code> - Delete book
        </div>

        <h2>🧪 Test with curl:</h2>
        <pre>
# Get all authors
curl http://localhost:5000/api/authors

# Create author
curl -X POST http://localhost:5000/api/authors \\
  -H "Content-Type: application/json" \\
  -d '{"name": "J.K. Rowling", "city": "London", "bio": "Author of Harry Potter"}'

# Get books with pagination
curl "http://localhost:5000/api/books?page=1&per_page=5&sort=title&order=asc"

# Create book
curl -X POST http://localhost:5000/api/books \\
  -H "Content-Type: application/json" \\
  -d '{"title": "New Book", "author_id": 1, "year": 2024}'

# Get single book
curl http://localhost:5000/api/books/1

# Update book
curl -X PUT http://localhost:5000/api/books/1 \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Updated Title"}'

# Delete book
curl -X DELETE http://localhost:5000/api/books/1
        </pre>
    </body>
    </html>
    '''


@app.route('/frontend')
def frontend():
    """Serve the modern frontend directly"""
    # Read and return the frontend.html file
    try:
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Book Management System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
            animation: fadeInDown 0.6s ease;
        }

        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            animation: fadeInUp 0.6s ease;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(0,0,0,0.3);
        }

        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .icon {
            width: 30px;
            height: 30px;
            display: inline-block;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
            font-size: 0.95em;
        }

        input, select, textarea {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: all 0.3s ease;
            font-family: inherit;
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        textarea {
            resize: vertical;
            min-height: 80px;
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }

        button:active {
            transform: translateY(0);
        }

        button.delete {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
            padding: 8px 16px;
            font-size: 0.9em;
        }

        button.edit {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
            padding: 8px 16px;
            font-size: 0.9em;
            margin-right: 8px;
        }

        .controls {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            margin-bottom: 20px;
            padding: 20px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            border-radius: 15px;
        }

        .controls label {
            margin: 0;
            font-size: 0.9em;
        }

        .controls select {
            width: auto;
            min-width: 150px;
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 20px;
            overflow: hidden;
            border-radius: 15px;
        }

        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }

        td {
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
        }

        tr:hover {
            background: #f8f9ff;
        }

        tr:last-child td {
            border-bottom: none;
        }

        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            margin-top: 25px;
            flex-wrap: wrap;
        }

        .pagination button {
            padding: 10px 20px;
        }

        .pagination span {
            color: #333;
            font-weight: 600;
        }

        .message {
            padding: 15px 20px;
            margin-bottom: 20px;
            border-radius: 10px;
            animation: slideIn 0.4s ease;
            font-weight: 500;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .success {
            background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
            color: #155724;
        }

        .error {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            color: #721c24;
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(5px);
            animation: fadeIn 0.3s ease;
        }

        .modal-content {
            background: white;
            margin: 5% auto;
            padding: 35px;
            border-radius: 20px;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: scaleIn 0.3s ease;
        }

        .close {
            float: right;
            font-size: 32px;
            font-weight: bold;
            cursor: pointer;
            color: #999;
            transition: color 0.3s ease;
            line-height: 1;
        }

        .close:hover {
            color: #667eea;
        }

        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }

        .stat-card {
            flex: 1;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }

        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes scaleIn {
            from {
                opacity: 0;
                transform: scale(0.9);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .header h1 {
                font-size: 2em;
            }

            .controls {
                flex-direction: column;
                align-items: stretch;
            }

            .controls select {
                width: 100%;
            }

            table {
                font-size: 0.9em;
            }
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }

        .empty-state svg {
            width: 100px;
            height: 100px;
            margin-bottom: 20px;
            opacity: 0.3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Book Management System</h1>
            <p>Manage your library with ease</p>
        </div>

        <div id="message" class="message" style="display:none;"></div>

        <div class="grid">
            <!-- Add Book Card -->
            <div class="card">
                <h2>
                    <span class="icon">📖</span>
                    Add New Book
                </h2>
                <form id="addBookForm">
                    <div class="form-group">
                        <label for="title">Title *</label>
                        <input type="text" id="title" placeholder="Enter book title" required>
                    </div>
                    <div class="form-group">
                        <label for="author_id">Author *</label>
                        <select id="author_id" required>
                            <option value="">Select an author</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="year">Publication Year</label>
                        <input type="number" id="year" placeholder="e.g., 2024" min="1000" max="2100">
                    </div>
                    <div class="form-group">
                        <label for="isbn">ISBN</label>
                        <input type="text" id="isbn" placeholder="e.g., 978-1234567890">
                    </div>
                    <button type="submit">Add Book</button>
                </form>
            </div>

            <!-- Add Author Card -->
            <div class="card">
                <h2>
                    <span class="icon">✍️</span>
                    Add New Author
                </h2>
                <form id="addAuthorForm">
                    <div class="form-group">
                        <label for="authorName">Name *</label>
                        <input type="text" id="authorName" placeholder="Enter author name" required>
                    </div>
                    <div class="form-group">
                        <label for="city">City</label>
                        <input type="text" id="city" placeholder="Author's city">
                    </div>
                    <div class="form-group">
                        <label for="bio">Biography</label>
                        <textarea id="bio" placeholder="Brief biography of the author"></textarea>
                    </div>
                    <button type="submit">Add Author</button>
                </form>
            </div>
        </div>

        <!-- Stats -->
        <div class="card">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="totalBooks">0</div>
                    <div class="stat-label">Total Books</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalAuthors">0</div>
                    <div class="stat-label">Total Authors</div>
                </div>
            </div>
        </div>

        <!-- Book List Card -->
        <div class="card">
            <h2>
                <span class="icon">📚</span>
                Book Collection
            </h2>
            
            <div class="controls">
                <div>
                    <label>Show:</label>
                    <select id="perPage" onchange="loadBooks()">
                        <option value="5">5 per page</option>
                        <option value="10" selected>10 per page</option>
                        <option value="20">20 per page</option>
                        <option value="50">50 per page</option>
                    </select>
                </div>
                
                <div>
                    <label>Sort by:</label>
                    <select id="sortBy" onchange="loadBooks()">
                        <option value="title">Title</option>
                        <option value="year">Year</option>
                        <option value="created_at">Date Added</option>
                    </select>
                </div>
                
                <div>
                    <label>Order:</label>
                    <select id="order" onchange="loadBooks()">
                        <option value="asc">Ascending</option>
                        <option value="desc">Descending</option>
                    </select>
                </div>
                
                <button onclick="loadBooks()">🔄 Refresh</button>
            </div>
            
            <div id="booksTable">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading books...</p>
                </div>
            </div>
            
            <div class="pagination" id="pagination"></div>
        </div>

        <!-- Author List Card -->
        <div class="card">
            <h2>
                <span class="icon">👥</span>
                Authors Directory
            </h2>
            <div id="authorsList">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading authors...</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Edit Book Modal -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal()">&times;</span>
            <h2>
                <span class="icon">✏️</span>
                Edit Book
            </h2>
            <form id="editBookForm">
                <input type="hidden" id="editId">
                <div class="form-group">
                    <label for="editTitle">Title *</label>
                    <input type="text" id="editTitle" required>
                </div>
                <div class="form-group">
                    <label for="editAuthorId">Author *</label>
                    <select id="editAuthorId" required>
                        <option value="">Select an author</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="editYear">Year</label>
                    <input type="number" id="editYear" min="1000" max="2100">
                </div>
                <div class="form-group">
                    <label for="editIsbn">ISBN</label>
                    <input type="text" id="editIsbn">
                </div>
                <button type="submit">Update Book</button>
            </form>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:5000/api';
        let currentPage = 1;

        async function loadAuthors() {
            try {
                const response = await fetch(`${API_BASE}/authors`);
                const data = await response.json();

                if (data.success) {
                    updateAuthorDropdown('author_id', data.authors);
                    updateAuthorDropdown('editAuthorId', data.authors);
                    
                    document.getElementById('totalAuthors').textContent = data.count;

                    const authorsList = document.getElementById('authorsList');
                    
                    if (data.authors.length === 0) {
                        authorsList.innerHTML = `
                            <div class="empty-state">
                                <p>No authors yet. Add your first author above!</p>
                            </div>
                        `;
                        return;
                    }

                    let html = '<table><thead><tr><th>ID</th><th>Name</th><th>City</th><th>Books</th><th>Actions</th></tr></thead><tbody>';

                    data.authors.forEach(author => {
                        html += `<tr>
                            <td><strong>${author.id}</strong></td>
                            <td>${author.name}</td>
                            <td>${author.city || '-'}</td>
                            <td><strong>${author.books_count}</strong></td>
                            <td>
                                <button class="edit" onclick="editAuthor(${author.id})">Edit</button>
                                <button class="delete" onclick="deleteAuthor(${author.id})">Delete</button>
                            </td>
                        </tr>`;
                    });

                    html += '</tbody></table>';
                    authorsList.innerHTML = html;
                }
            } catch (error) {
                showMessage('Error loading authors: ' + error.message, 'error');
            }
        }

        function updateAuthorDropdown(selectId, authors) {
            const select = document.getElementById(selectId);
            const currentValue = select.value;
            select.innerHTML = '<option value="">Select an author</option>';

            authors.forEach(author => {
                const option = document.createElement('option');
                option.value = author.id;
                option.textContent = author.name;
                select.appendChild(option);
            });

            if (currentValue) {
                select.value = currentValue;
            }
        }

        async function loadBooks(page = 1) {
            currentPage = page;
            const perPage = document.getElementById('perPage').value;
            const sortBy = document.getElementById('sortBy').value;
            const order = document.getElementById('order').value;

            try {
                const response = await fetch(
                    `${API_BASE}/books?page=${page}&per_page=${perPage}&sort=${sortBy}&order=${order}`
                );
                const data = await response.json();

                if (data.success) {
                    document.getElementById('totalBooks').textContent = data.count;

                    const booksTable = document.getElementById('booksTable');
                    
                    if (data.books.length === 0) {
                        booksTable.innerHTML = `
                            <div class="empty-state">
                                <p>No books found. Add your first book above!</p>
                            </div>
                        `;
                        document.getElementById('pagination').innerHTML = '';
                        return;
                    }

                    let html = '<table><thead><tr><th>ID</th><th>Title</th><th>Author</th><th>Year</th><th>ISBN</th><th>Actions</th></tr></thead><tbody>';

                    data.books.forEach(book => {
                        html += `<tr>
                            <td><strong>${book.id}</strong></td>
                            <td>${book.title}</td>
                            <td>${book.author_name}</td>
                            <td>${book.year || '-'}</td>
                            <td>${book.isbn || '-'}</td>
                            <td>
                                <button class="edit" onclick="openEditModal(${book.id})">Edit</button>
                                <button class="delete" onclick="deleteBook(${book.id})">Delete</button>
                            </td>
                        </tr>`;
                    });

                    html += '</tbody></table>';
                    booksTable.innerHTML = html;

                    const pagination = document.getElementById('pagination');
                    let paginationHtml = '';

                    if (data.has_prev) {
                        paginationHtml += `<button onclick="loadBooks(${page - 1})">← Previous</button>`;
                    }

                    paginationHtml += `<span>Page ${data.page} of ${data.pages}</span>`;

                    if (data.has_next) {
                        paginationHtml += `<button onclick="loadBooks(${page + 1})">Next →</button>`;
                    }

                    pagination.innerHTML = paginationHtml;
                }
            } catch (error) {
                showMessage('Error loading books: ' + error.message, 'error');
            }
        }

        document.getElementById('addBookForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = {
                title: document.getElementById('title').value,
                author_id: parseInt(document.getElementById('author_id').value),
                year: document.getElementById('year').value ? parseInt(document.getElementById('year').value) : null,
                isbn: document.getElementById('isbn').value || null
            };

            try {
                const response = await fetch(`${API_BASE}/books`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('✅ Book added successfully!', 'success');
                    this.reset();
                    loadBooks(currentPage);
                    loadAuthors();
                } else {
                    showMessage('❌ Error: ' + data.error, 'error');
                }
            } catch (error) {
                showMessage('❌ Error: ' + error.message, 'error');
            }
        });

        document.getElementById('addAuthorForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = {
                name: document.getElementById('authorName').value,
                city: document.getElementById('city').value || null,
                bio: document.getElementById('bio').value || null
            };

            try {
                const response = await fetch(`${API_BASE}/authors`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('✅ Author added successfully!', 'success');
                    this.reset();
                    loadAuthors();
                } else {
                    showMessage('❌ Error: ' + data.error, 'error');
                }
            } catch (error) {
                showMessage('❌ Error: ' + error.message, 'error');
            }
        });

        async function deleteBook(id) {
            if (!confirm('Are you sure you want to delete this book?')) return;

            try {
                const response = await fetch(`${API_BASE}/books/${id}`, { method: 'DELETE' });
                const data = await response.json();

                if (data.success) {
                    showMessage('✅ Book deleted successfully!', 'success');
                    loadBooks(currentPage);
                    loadAuthors();
                } else {
                    showMessage('❌ Error: ' + data.error, 'error');
                }
            } catch (error) {
                showMessage('❌ Error: ' + error.message, 'error');
            }
        }

        async function deleteAuthor(id) {
            if (!confirm('Are you sure you want to delete this author and all their books?')) return;

            try {
                const response = await fetch(`${API_BASE}/authors/${id}`, { method: 'DELETE' });
                const data = await response.json();

                if (data.success) {
                    showMessage('✅ Author and associated books deleted successfully!', 'success');
                    loadAuthors();
                    loadBooks(currentPage);
                } else {
                    showMessage('❌ Error: ' + data.error, 'error');
                }
            } catch (error) {
                showMessage('❌ Error: ' + error.message, 'error');
            }
        }

        async function openEditModal(bookId) {
            try {
                const response = await fetch(`${API_BASE}/books/${bookId}`);
                const data = await response.json();

                if (data.success) {
                    const book = data.book;
                    document.getElementById('editId').value = book.id;
                    document.getElementById('editTitle').value = book.title;
                    document.getElementById('editYear').value = book.year || '';
                    document.getElementById('editIsbn').value = book.isbn || '';

                    const authorsResponse = await fetch(`${API_BASE}/authors`);
                    const authorsData = await authorsResponse.json();

                    if (authorsData.success) {
                        const select = document.getElementById('editAuthorId');
                        select.innerHTML = '<option value="">Select an author</option>';

                        authorsData.authors.forEach(author => {
                            const option = document.createElement('option');
                            option.value = author.id;
                            option.textContent = author.name;
                            option.selected = (author.id === book.author_id);
                            select.appendChild(option);
                        });
                    }

                    document.getElementById('editModal').style.display = 'block';
                }
            } catch (error) {
                showMessage('❌ Error loading book details: ' + error.message, 'error');
            }
        }

        function closeModal() {
            document.getElementById('editModal').style.display = 'none';
        }

        document.getElementById('editBookForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const bookId = document.getElementById('editId').value;
            const formData = {
                title: document.getElementById('editTitle').value,
                author_id: parseInt(document.getElementById('editAuthorId').value),
                year: document.getElementById('editYear').value ? parseInt(document.getElementById('editYear').value) : null,
                isbn: document.getElementById('editIsbn').value || null
            };

            try {
                const response = await fetch(`${API_BASE}/books/${bookId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('✅ Book updated successfully!', 'success');
                    closeModal();
                    loadBooks(currentPage);
                } else {
                    showMessage('❌ Error: ' + data.error, 'error');
                }
            } catch (error) {
                showMessage('❌ Error: ' + error.message, 'error');
            }
        });

        async function editAuthor(authorId) {
            try {
                const response = await fetch(`${API_BASE}/authors/${authorId}`);
                const data = await response.json();

                if (data.success) {
                    const author = data.author;
                    
                    const newName = prompt('Enter new name for author:', author.name);
                    const newCity = prompt('Enter new city for author:', author.city || '');
                    const newBio = prompt('Enter new biography for author:', author.bio || '');
                    
                    if (!newName || newName === author.name) return;

                    const updateData = { name: newName };
                    if (newCity !== null) updateData.city = newCity;
                    if (newBio !== null) updateData.bio = newBio;

                    const updateResponse = await fetch(`${API_BASE}/authors/${authorId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(updateData)
                    });

                    const updateDataResult = await updateResponse.json();

                    if (updateDataResult.success) {
                        showMessage('✅ Author updated successfully!', 'success');
                        loadAuthors();
                        loadBooks(currentPage);
                    } else {
                        showMessage('❌ Error: ' + updateDataResult.error, 'error');
                    }
                }
            } catch (error) {
                showMessage('❌ Error: ' + error.message, 'error');
            }
        }

        function showMessage(text, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = text;
            messageDiv.className = `message ${type}`;
            messageDiv.style.display = 'block';

            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }

        window.onclick = function(event) {
            const modal = document.getElementById('editModal');
            if (event.target === modal) {
                closeModal();
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            loadAuthors();
            loadBooks();
        });
    </script>
</body>
</html>
        '''
    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error Loading Frontend</title>
            <style>
                body {{ 
                    font-family: Arial; 
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    height: 100vh; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                }}
                .message {{
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    text-align: center;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                }}
                h1 {{ color: #e74c3c; }}
                p {{ color: #666; margin: 20px 0; }}
                .error {{
                    color: #e74c3c;
                    background: #fee;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="message">
                <h1>⚠️ Error Loading Frontend</h1>
                <div class="error">Error: {str(e)}</div>
                <p>Please check that the frontend code is embedded in the Flask app.</p>
            </div>
        </body>
        </html>
        '''

# =============================================================================
# INITIALIZE DATABASE WITH SAMPLE DATA
# =============================================================================

def init_db():
    with app.app_context():
        db.create_all()

        # Check if we have any authors
        if Author.query.count() == 0:
            # Create some sample authors
            sample_authors = [
                Author(name='Eric Matthes', city='Anchorage', bio='Python educator and author'),
                Author(name='Miguel Grinberg', city='Portland', bio='Flask expert and software engineer'),
                Author(name='Robert C. Martin', city='Illinois', bio='Software engineer and author'),
                Author(name='J.K. Rowling', city='London', bio='Author of Harry Potter series'),
                Author(name='George Orwell', city='London', bio='English novelist and essayist'),
            ]
            db.session.add_all(sample_authors)
            db.session.commit()
            print('✅ Sample authors added!')

        # Check if we have any books
        if Book.query.count() == 0:
            # Get author IDs
            authors = {author.name: author.id for author in Author.query.all()}
            
            sample_books = [
                Book(title='Python Crash Course', author_id=authors['Eric Matthes'], year=2019, isbn='978-1593279288'),
                Book(title='Flask Web Development', author_id=authors['Miguel Grinberg'], year=2018, isbn='978-1491991732'),
                Book(title='Clean Code', author_id=authors['Robert C. Martin'], year=2008, isbn='978-0132350884'),
                Book(title='Harry Potter and the Philosopher\'s Stone', author_id=authors['J.K. Rowling'], year=1997, isbn='978-0747532743'),
                Book(title='1984', author_id=authors['George Orwell'], year=1949, isbn='978-0451524935'),
                Book(title='Animal Farm', author_id=authors['George Orwell'], year=1945, isbn='978-0451526342'),
                Book(title='Python for Everybody', author_id=authors['Eric Matthes'], year=2016, isbn='978-1530051120'),
                Book(title='Flask API Development', author_id=authors['Miguel Grinberg'], year=2021, isbn='978-1484270894'),
            ]
            db.session.add_all(sample_books)
            db.session.commit()
            print('✅ Sample books added!')
        
        print('🚀 Database initialized successfully!')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)


# =============================================================================
# REST API CONCEPTS:
# =============================================================================
#
# HTTP Method | CRUD      | Typical Use
# ------------|-----------|---------------------------
# GET         | Read      | Retrieve data
# POST        | Create    | Create new resource
# PUT         | Update    | Update entire resource
# PATCH       | Update    | Update partial resource
# DELETE      | Delete    | Remove resource
#
# =============================================================================
# HTTP STATUS CODES:
# =============================================================================
#
# Code | Meaning
# -----|------------------
# 200  | OK (Success)
# 201  | Created
# 400  | Bad Request (client error)
# 404  | Not Found
# 500  | Internal Server Error
#
# =============================================================================
# KEY FUNCTIONS:
# =============================================================================
#
# jsonify()           - Convert Python dict to JSON response
# request.get_json()  - Get JSON data from request body
# request.args.get()  - Get query parameters (?key=value)
#
# =============================================================================


# =============================================================================
# EXERCISE:
# =============================================================================
#
# 1. Create new class say "Author" with fields id, name, bio, city with its table. 
# Write all CRUD api routes for it similar to Book class.
# Additionally try to link Book and Author class such that each book has one author and one author can have multiple books.

# 1. Create 2 simple frontend using JavaScript fetch()
# This is a bigger exercise. Create a frontend in HTML and JS that uses all api routes and displays data dynamically, along with create/edit/delete functionality.
# Since the API is through n through accessible on the computer/server, you don't need to use render_template from flask, instead, 
# you can directly use ipaddress:portnumber/apiroute from any where. So your HTML JS code can be anywhere on computer (not necessarily in flask)  

# 3. Add pagination: `/api/books?page=1&per_page=10` 
# Hint - the sqlalchemy provides paginate method. 
# OPTIONAL - For ease of understanding, create a new api say /api/books-with-pagination which takes page number and number of books per page

# 4. Add sorting: `/api/books?sort=title&order=desc`
# OPTIONAL - For ease of understanding, create a new api say /api/books-with-sorting
#
# =============================================================================