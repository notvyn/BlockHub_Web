# 1. Import create_app instead of app
from app import create_app, db
from app.models import Tag, Course

# 2. Build the app using your factory function
app = create_app()

# Your default CS 2103 tags
default_tags = [
    # --- Officer/Admin Tags ---
    {'name': 'Class Representative', 'category': 'Role'},
    {'name': 'Class Vice Representative', 'category': 'Role'},
    {'name': 'Secretary', 'category': 'Role'},
    {'name': 'Treasurer', 'category': 'Role'},

    # --- Aspiring Fields & Technical Tracks ---
    {'name': 'Aspiring Cybersecurity Analyst', 'category': 'Technical'},
    {'name': 'Aspiring Data Scientist', 'category': 'Technical'},
    {'name': 'Aspiring AI/ML Engineer', 'category': 'Technical'},
    {'name': 'Aspiring Game Developer', 'category': 'Technical'},
    {'name': 'Aspiring Web Developer', 'category': 'Technical'},
    {'name': 'Aspiring Full Stack Developer', 'category': 'Technical'},
    {'name': 'Python Developer', 'category': 'Technical'},
    {'name': 'C++ Developer', 'category': 'Technical'},
    {'name': 'Java Developer', 'category': 'Technical'},

    # --- New Additions: Interests ---
    {'name': 'Bookworm', 'category': 'Interest'},
    {'name': 'Foodie', 'category': 'Interest'},
    {'name': 'Fitness Enthusiast', 'category': 'Interest'},
    {'name': 'Traveler', 'category': 'Interest'},
    {'name': 'Photographer', 'category': 'Interest'},
    {'name': 'Pet Lover', 'category': 'Interest'},
    {'name': 'Movie Buff', 'category': 'Interest'},
    {'name': 'Early Bird', 'category': 'Interest'},
    {'name': 'Night Owl', 'category': 'Interest'},
    {'name': 'Coffee Addict', 'category': 'Interest'},
    {'name': 'Gamer', 'category': 'Interest'},
    {'name': 'Music Lover', 'category': 'Interest'},
    {'name': 'Artist', 'category': 'Interest'}
]

courses_2103 = [
    {'code': 'AI 101', 'title': 'Linear Algebra for AI', 'units': 3.00, 'instructor': "Ma'am Maria Kathleen Joan P. Abacan"},
    {'code': 'CC 104', 'title': 'Information Management', 'units': 3.00, 'instructor': "Ma'am Jeleen M. Mangubat"},
    {'code': 'GEd 105', 'title': 'Readings in Philippine History', 'units': 3.00, 'instructor': "Ma'am Jhamil L. Amponin"},
    {'code': 'GEd 107', 'title': 'Ethics', 'units': 3.00, 'instructor': "Ma'am Rica Anne L. Hidalgo"},
    {'code': 'OOP 101', 'title': 'Object-Oriented Programming', 'units': 3.00, 'instructor': "Ma'am Fatima Marie P. Agdon"},
    {'code': 'CpE 405', 'title': 'Discrete Mathematics', 'units': 3.00, 'instructor': "Ma'am Alondra C. De Villa"},
    {'code': 'PATHFit 3', 'title': 'Choice of Dance, Sports, Martial Arts, Group Exercise and Outdoor and Adventure Activities 1', 'units': 2.00, 'instructor': "Ma'am Sapryl N. Bueno"},
    {'code': 'PHYS 111', 'title': 'General Physics 1', 'units': 3.00, 'instructor': "Ma'am Baby Karen L. Mendoza"},
]

# 3. Use the newly created app to open the context
with app.app_context():
    for tag_data in default_tags:
        # Check if it already exists so we don't cause an error
        existing_tag = Tag.query.filter_by(name=tag_data['name']).first()
        if not existing_tag:
            new_tag = Tag(name=tag_data['name'], category=tag_data['category'])
            db.session.add(new_tag)

    for course in courses_2103:
        existing_course = Course.query.filter_by(code=course['code']).first()
        if not existing_course:
            new_course = Course(code=course['code'], title=course['title'], units=course['units'], instructor=course['instructor'])
            db.session.add(new_course)
            
    db.session.commit()
    print("Tags successfully seeded!")
    print("Course successfully seeded!")