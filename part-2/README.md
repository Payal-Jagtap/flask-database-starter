# Part 2: Full CRUD Operations with HTML Forms

## One-Line Summary
Full CRUD operations (Create, Read, Update, Delete) with HTML forms

## What You'll Learn
- HTML forms with POST method
- Getting form data with `request.form`
- UPDATE and DELETE SQL commands
- `redirect()` and `url_for()` functions
- Flash messages for user feedback

## Prerequisites
- Complete part-1 first
- Understand basic database connection

## How to Run
```bash
cd part-2
python app.py
```
Open: http://localhost:5000

## CRUD Operations Explained

| Operation | HTTP Method | SQL Command | Route | Description |
|-----------|-------------|-------------|-------|-------------|
| **C**reate | POST | INSERT INTO | `/add` | Add new student |
| **R**ead | GET | SELECT | `/` | Display all students |
| **U**pdate | POST | UPDATE | `/edit/<id>` | Modify existing student |
| **D**elete | GET | DELETE | `/delete/<id>` | Remove student |

## Key Files
```
part-2/
├── app.py              <- CRUD operations
├── templates/
│   ├── index.html      <- List all students with Edit/Delete buttons
│   ├── add.html        <- Form to add new student
│   └── edit.html       <- Form to edit existing student
└── README.md
```

## New Concepts

### 1. Form Handling
```python
@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':  # Form submitted
        name = request.form['name']  # Get form data
```

### 2. Redirect After Action
```python
return redirect(url_for('index'))  # Go to home page
```

### 3. Flash Messages
```python
flash('Student added!', 'success')  # Show message once
```

## Exercise
1. Add a "Search" feature to find students by name
2. Add validation to check if email already exists before adding

## Next Step
→ Go to **part-3** to learn Flask-SQLAlchemy ORM (cleaner database code!)
