import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'jobportal_secret_2024')
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''  # XAMPP default
    DB_NAME = 'job_portal_db'

    # Flask-Mail (configure with your SMTP)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your_app_password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', 'noreply@jobportal.com')
