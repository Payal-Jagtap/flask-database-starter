"""
Part 3: Flask-SQLAlchemy ORM
============================
Say goodbye to raw SQL! Use Python classes to work with databases.

What You'll Learn:
- Setting up Flask-SQLAlchemy
- Creating Models (Python classes = database tables)
- ORM queries instead of raw SQL
- Relationships between tables (One-to-Many)

Prerequisites: Complete part-1 and part-2
Install: pip install flask-sqlalchemy
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy  # Import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'  # Database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable warning

db = SQLAlchemy(app)  # Initialize SQLAlchemy with app


# =============================================================================
# MODELS (Python Classes = Database Tables)
# =============================================================================

class Course(db.Model):  # Course table
    id = db.Column(db.Integer, primary_key=True)  # Auto-increment ID
    name = db.Column(db.String(100), nullable=False)  # Course name
    description = db.Column(db.Text)  # Optional description

    # Relationship: One Course has Many Students
    students = db.relationship('Student', backref='course', lazy=True)
    teachers = db.relationship('Teacher', backref='course', lazy=True)

    def __repr__(self):  # How to display this object
        return f'<Course {self.name}>'


class Student(db.Model):  # Student table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  # unique=True means no duplicates

    # Foreign Key: Links student to a course
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'

class Teacher(db.Model):  # Teacher table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    specialization = db.Column(db.String(100))  # Additional field for teachers
    
    # Foreign Key: One Teacher teaches one Course
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    def __repr__(self):
        return f'<Teacher {self.name}>'

# =============================================================================
# ROUTES - Using ORM instead of raw SQL
# =============================================================================

@app.route('/')
def index():
    # OLD WAY (raw SQL): conn.execute('SELECT * FROM students').fetchall()
    # NEW WAY (ORM):
    students = Student.query.all()  # Get all students
    return render_template('index.html', students=students)


@app.route('/courses')
def courses():
    all_courses = Course.query.all()  # Get all courses
    return render_template('courses.html', courses=all_courses)


@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course_id = request.form['course_id']

        # OLD WAY: conn.execute('INSERT INTO students...')
        # NEW WAY:
        new_student = Student(name=name, email=email, course_id=course_id)  # Create object
        db.session.add(new_student)  # Add to session
        db.session.commit()  # Save to database

        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))

    courses = Course.query.all()  # Get courses for dropdown
    return render_template('add.html', courses=courses)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    # OLD WAY: conn.execute('SELECT * FROM students WHERE id = ?', (id,))
    # NEW WAY:
    student = Student.query.get_or_404(id)  # Get by ID or show 404 error

    if request.method == 'POST':
        student.name = request.form['name']  # Just update the object
        student.email = request.form['email']
        student.course_id = request.form['course_id']

        db.session.commit()  # Save changes
        flash('Student updated!', 'success')
        return redirect(url_for('index'))

    courses = Course.query.all()
    return render_template('edit.html', student=student, courses=courses)


@app.route('/delete/<int:id>')
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)  # Delete the object
    db.session.commit()

    flash('Student deleted!', 'danger')
    return redirect(url_for('index'))


# =============================================================================
# TEACHER ROUTES - NEW
# =============================================================================

@app.route('/teachers')
def teachers():
    """List all teachers"""
    all_teachers = Teacher.query.all()
    return render_template('teachers.html', teachers=all_teachers)


@app.route('/add-teacher', methods=['GET', 'POST'])
def add_teacher():
    """Add new teacher"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        specialization = request.form.get('specialization', '')
        course_id = request.form['course_id']
        new_teacher = Teacher(
            name=name, 
            email=email, 
            specialization=specialization,
            course_id=course_id
        )
        db.session.add(new_teacher)
        db.session.commit()

        flash('Teacher added successfully!', 'success')
        return redirect(url_for('teachers'))

    courses = Course.query.all()
    return render_template('add_teacher.html', courses=courses)

@app.route('/edit-teacher/<int:id>', methods=['GET', 'POST'])
def edit_teacher(id):
    """Edit teacher"""
    teacher = Teacher.query.get_or_404(id)

    if request.method == 'POST':
        teacher.name = request.form['name']
        teacher.email = request.form['email']
        teacher.specialization = request.form.get('specialization', '')
        teacher.course_id = request.form['course_id']

        db.session.commit()
        flash('Teacher updated!', 'success')
        return redirect(url_for('teachers'))

    courses = Course.query.all()
    return render_template('edit_teacher.html', teacher=teacher, courses=courses)
@app.route('/delete-teacher/<int:id>')
def delete_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    db.session.delete(teacher)
    db.session.commit()

    flash('Teacher deleted!', 'danger')
    return redirect(url_for('teachers'))



@app.route('/add-course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')  # Optional field

        new_course = Course(name=name, description=description)
        db.session.add(new_course)
        db.session.commit()

        flash('Course added!', 'success')
        return redirect(url_for('courses'))

    return render_template('add_course.html')

#=============================================================================
# ADVANCED QUERY EXAMPLES - EXERCISE 2
# =============================================================================

@app.route('/query-examples')
def query_examples():
    """Demonstrate different query methods"""
    
    # Example 1: Filter by course
    python_course = Course.query.filter_by(name='Python Basics').first()
    if python_course:
        python_students = Student.query.filter_by(course_id=python_course.id).all()
    else:
        python_students = []
    
    # Example 2: Order by name
    students_ordered = Student.query.order_by(Student.name).all()
    
    # Example 3: Limit results
    first_three_students = Student.query.limit(3).all()
    
    # Example 4: Filter with LIKE (case-insensitive search)
    students_with_a = Student.query.filter(Student.name.like('%a%')).all()
    
    # Example 5: Count
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    
    # Example 6: Complex filter (students in courses with 'Python' in name)
    students_in_python = Student.query.join(Course).filter(
        Course.name.like('%Python%')
    ).all()
    
    return render_template('query_examples.html', 
                         python_students=python_students,
                         students_ordered=students_ordered,
                         first_three=first_three_students,
                         students_with_a=students_with_a,
                         total_students=total_students,
                         total_teachers=total_teachers,
                         students_in_python=students_in_python)


# =============================================================================
# CREATE TABLES AND ADD SAMPLE DATA
# =============================================================================

def init_db():
    """Create tables and add sample courses if empty"""
    with app.app_context():
        db.create_all()  # Create all tables based on models

        # Add sample courses if none exist
        if Course.query.count() == 0:
            sample_courses = [
                Course(name='Python Basics', description='Learn Python programming fundamentals'),
                Course(name='Web Development', description='HTML, CSS, JavaScript and Flask'),
                Course(name='Data Science', description='Data analysis with Python'),
            ]
            db.session.add_all(sample_courses)  # Add multiple at once
            db.session.commit()
            print('Sample courses added!')

        # Add sample teachers if none exist
        if Teacher.query.count() == 0:
            courses = Course.query.all()
            sample_teachers = [
                Teacher(name='Dr. Sarah Johnson', email='sarah@school.com', 
                       specialization='Python Programming', course_id=courses[0].id),
                Teacher(name='Prof. Mike Chen', email='mike@school.com', 
                       specialization='Full Stack Development', course_id=courses[1].id),
                Teacher(name='Dr. Emily Brown', email='emily@school.com', 
                       specialization='Data Analytics', course_id=courses[2].id),
            ]
            db.session.add_all(sample_teachers)
            db.session.commit()
            print('✓ Sample teachers added!')

        # Add sample students if none exist
        if Student.query.count() == 0:
            courses = Course.query.all()
            sample_students = [
                Student(name='Alice Smith', email='alice@student.com', course_id=courses[0].id),
                Student(name='Bob Johnson', email='bob@student.com', course_id=courses[1].id),
                Student(name='Charlie Davis', email='charlie@student.com', course_id=courses[0].id),
                Student(name='Diana Wilson', email='diana@student.com', course_id=courses[2].id),
            ]
            db.session.add_all(sample_students)
            db.session.commit()
            print('✓ Sample students added!')



if __name__ == '__main__':
    init_db()
    app.run(debug=True)


# =============================================================================
# ORM vs RAW SQL COMPARISON:
# =============================================================================
#
# Operation      | Raw SQL                          | SQLAlchemy ORM
# ---------------|----------------------------------|---------------------------
# Get all        | SELECT * FROM students           | Student.query.all()
# Get by ID      | SELECT * WHERE id = ?            | Student.query.get(id)
# Filter         | SELECT * WHERE name = ?          | Student.query.filter_by(name='John')
# Insert         | INSERT INTO students VALUES...   | db.session.add(student)
# Update         | UPDATE students SET...           | student.name = 'New'; db.session.commit()
# Delete         | DELETE FROM students WHERE...    | db.session.delete(student)
#
# =============================================================================
# COMMON QUERY METHODS:
# =============================================================================
#
# Student.query.all()                    - Get all records
# Student.query.first()                  - Get first record
# Student.query.get(1)                   - Get by primary key
# Student.query.get_or_404(1)            - Get or show 404 error
# Student.query.filter_by(name='John')   - Filter by exact value
# Student.query.filter(Student.name.like('%john%'))  - Filter with LIKE
# Student.query.order_by(Student.name)   - Order results
# Student.query.count()                  - Count records
#
# =============================================================================


# =============================================================================
# EXERCISE:
# =============================================================================
#
# 1. Add a `Teacher` model with a relationship to Course 
# (have one Course can be taught by many Teachers and one Teacher can only teach only one Course)
# In other words, create new Teacher model exactly like Student with all others things same 
# (relationship between the two, frontend page for teacher list, add new teacher, backend routes for add new teacher, edit teacher, delete teacher)
# Additional exercise - display list of students with course name and teacher name (taken from the course name) and vice versa

# 2. Try different query methods: `filter()`, `order_by()`, `limit()`
#
# =============================================================================
