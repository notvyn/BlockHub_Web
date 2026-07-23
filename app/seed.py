from app import app, db
from app.models import Tag

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

with app.app_context():
    for tag_data in default_tags:
        # Check if it already exists so we don't cause an error
        existing_tag = Tag.query.filter_by(name=tag_data['name']).first()
        if not existing_tag:
            new_tag = Tag(name=tag_data['name'], category=tag_data['category'])
            db.session.add(new_tag)
            
    db.session.commit()
    print("Tags successfully seeded!")