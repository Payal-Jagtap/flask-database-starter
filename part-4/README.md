# Part 4: REST API with Flask

## One-Line Summary
REST API with Flask for database operations (JSON responses)

## What You'll Learn
- REST API concepts (GET, POST, PUT, DELETE)
- JSON responses with `jsonify()`
- API error handling and status codes
- Query parameters for filtering
- Testing APIs with curl

## Prerequisites
- Complete part-3 (Flask-SQLAlchemy)

## How to Run
```bash
cd part-6
python app.py
```
Open: http://localhost:5000

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/books` | Get all books |
| GET | `/api/books/<id>` | Get single book |
| POST | `/api/books` | Create new book |
| PUT | `/api/books/<id>` | Update book |
| DELETE | `/api/books/<id>` | Delete book |
| GET | `/api/books/search?q=<title>` | Search books |

## HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Invalid data |
| 404 | Not Found | Resource doesn't exist |

## Testing with curl

```bash
# Get all books
curl http://localhost:5000/api/books

# Get single book
curl http://localhost:5000/api/books/1

# Create a book
curl -X POST http://localhost:5000/api/books -H "Content-Type: application/json" -d '{"title": "New Book", "author": "Author Name", "year": 2024}'

# Update a book
curl -X PUT http://localhost:5000/api/books/1 -H "Content-Type: application/json" -d '{"year": 2025}'

# Delete a book
curl -X DELETE http://localhost:5000/api/books/1

# Search books
curl "http://localhost:5000/api/books/search?q=python&author=eric"
```

## Key Concepts

### JSON Response
```python
return jsonify({
    'success': True,
    'data': {...}
}), 200  # Status code
```

### Getting Request Data
```python
# JSON body (POST/PUT)
data = request.get_json()

# Query parameters (?key=value)
value = request.args.get('key')
```

### Model to Dictionary
```python
def to_dict(self):
    return {
        'id': self.id,
        'title': self.title,
        # ...
    }
```

## Key Files
```
part-6/
├── app.py              <- REST API routes
└── README.md
```

## API Response Format
```json
{
    "success": true,
    "message": "Optional message",
    "data": { ... }
}
```

## Exercise
1. Add pagination: `/api/books?page=1&per_page=10`
2. Add sorting: `/api/books?sort=title&order=desc`
3. Create a simple frontend using JavaScript fetch()

## Next Step
→ Go to **part-5** to learn PostgreSQL/MySQL configuration