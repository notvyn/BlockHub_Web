from app import app, db
from app.models import Tag

# Your default CS 2103 tags
default_tags = [
    {'name': 'Class Representative', 'category': 'Role'},
    {'name': 'Lead Developer', 'category': 'Role'},
    {'name': 'C++ Guru', 'category': 'Technical'},
    {'name': 'Python Specialist', 'category': 'Technical'},
    {'name': 'Frontend Designer', 'category': 'Technical'},
    {'name': 'Gamer', 'category': 'Interest'},
    {'name': 'Hardware Enthusiast', 'category': 'Interest'},
    {'name': 'Night Owl', 'category': 'Interest'}
]

with app.app_context():
    for tag_data in default_tags:
        # Check if it already exists so we don't cause an error
        existing_tag = Tag.query.filter_by(name=tag_data['name']).first()
        if not existing_tag:
            new_tag = Tag(name=tag_data['name'], category=tag_data['category'])
            db.session.add(new_tag)
            
    db.session.commit()
    print("Tags successfully seeded!")