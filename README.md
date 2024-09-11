# Facial Authentication Using Django

This project implements a facial authentication system using Django, OpenCV, and MySQL. Users can register with their facial images, which are stored and used for login authentication.

## Features

- User registration with facial recognition.
- Secure document upload with encryption.
- Admin dashboard for managing users and documents.
- User profile and document viewing functionalities.

## Prerequisites

- Python 3.x
- Django
- OpenCV
- MySQL
- `cryptography` package
- `PIL` (Pillow) package

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/facial-authentication-django.git
cd facial-authentication-django
cd facial_login
pip install -r requirements.txt
python manage.py runserver
