# KomSy3 (formerly BlockHub)

A centralized class management platform dedicated to bringing blockmates together. 

KomSy3 is designed to streamline academic communication, track upcoming deadlines, and provide a unified dashboard for class announcements and resources. It ensures that students stay informed while giving class officers an efficient tool to manage information.

## ❓ Why I built it

This project was deeply inspired by my experience as a Class Representative. It all started with a simple question: 'What happens to the students who aren't present during a lecture? How can they catch up on what they missed?' That's when it clicked. We had been using a basic spreadsheet tracker during our first year, but I took the initiative to build a dedicated web app for my block. KomSy3 was built to preserve resources, keep everyone informed, and make navigating the semester much easier for every student.

## ✨ Key Features

* **Centralized Announcements:** A live dashboard for important class updates and news.
* **Interactive Deadlines:** Track upcoming quizzes, activities, and requirements by course.
* **Core Courses & Master Schedule:** Centralized tracking for academic subjects, schedules, and instructor details.
* **Accessible Class Summaries**: Review record of lectures and takeaways on a specific day. 
* **Role-Based Access:** Distinct privileges for regular students and class officers/representatives to manage content securely.
* **Secure Feedback System:** Allows students to communicate concerns efficiently.
* **Custom Tools:** Includes a built-in lock-screen generator and customizable user profiles.

## 🛠️ Tech Stack

**Frontend:**
* HTML5
* CSS3 & Bootstrap
* Vanilla JavaScript
* Jinja2 Templating

**Backend:**
* Python
* Flask (Web Framework)
* SQLite (Database)
* SQLAlchemy (ORM)

## 📂 Project Structure

```text
KomSy3/
├── app/
│   ├── main/           # Core application routes (Dashboard, Deadlines, etc.)
│   ├── api/            # Silent json interaction routes (Live Search, Delete, etc.)
│   ├── auth/           # User Authentication (Login, Signup, Logout) 
│   ├── static/         # CSS, JavaScript, and Image files
│   ├── templates/      # HTML Jinja templates
│   ├── __init__.py     # App factory and configuration
│   └── models.py       # SQLAlchemy database schemas
├── .env                # Environment variables (Secret Key, DB URI) - Not tracked by git
├── requirements.txt    # Python dependencies
└── run.py              # Main entry point to launch the server
```

## 🚀 How to Clone and Run Locally
Follow these steps to set up a local development environment.

### 1. Clone the repository

```Bash
git clone [https://github.com/notvyn/BlockHub_Web.git](https://github.com/notvyn/BlockHub_Web.git)

cd BlockHub_Web
```

### 2. Create and activate a virtual environment

```Bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```Bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory and add your required keys:

```env
SECRET_KEY=your_secret_key_here

# Cloudinary Setup for Image Uploads
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here

# VAPID Keys for Push Notifications
VAPID_PUBLIC_KEY=your_vapid_public_key_here
VAPID_PRIVATE_KEY=your_vapid_private_key_here
VAPID_CLAIM_EMAIL=mailto:your_email@example.com

# Email Configuration
EMAIL_USER=your_email@example.com
EMAIL_PASS=your_email_app_password_here
```
*Note: To run this project fully, you will need to create a free Cloudinary Account for the image API, generate VAPID keys using an online VAPID generator, and generate an App Password from your email provider.*


### 5. Initialize the database

```Bash
python
>>> from run import app
>>> from app import db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 6. Run the application

```Bash
flask run
```

The site will be available at `http://127.0.0.1:5000`

## 🧠 What I Have Learned
Building KomSy3 has been a deep dive into full-stack development and project management. Here are a few key takeaways from this journey:

- Architecting a Full-Stack Application: Learned how to seamlessly connect a Vanilla JS/Bootstrap frontend with a Python-Flask backend using Jinja templates.

- Database Management: Gained hands-on experience designing relational data models with SQLite and SQLAlchemy to handle users, announcements, and courses.

- Deployment & Server Setup: Successfully navigated the challenges of deploying a live web application, managing virtual environments on a cloud Linux server (PythonAnywhere), and securely handling environment variables.

- Program Debugging & Logic Testing: Trained Problem Solving skills through code debugging and logic creation of both frontend and backend elements interaction.  

- Scoping & Agile Principles: Discovered the importance of building a Minimum Viable Product (MVP) and managing "feature creep" to ensure a timely and functional launch.

- Structure & Code Optimization: Realized the significance of writing modular code using DRY Principle (Do Not Repeat Yourself) and maintaining simplicity and directory accessibility.

<hr>

A passion project brought to life by **John Calvin Samson**. Built by a student, for students.