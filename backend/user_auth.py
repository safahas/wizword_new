import json
import os
import bcrypt
from typing import Optional
import secrets
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Force load .env from absolute path
load_dotenv(dotenv_path="C:/Users/CICD Student/cursor ai agent/game_guess/.env")

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')
TEMP_PASSWORDS_FILE = os.path.join(os.path.dirname(__file__), 'temp_passwords.json')

# Helper to load all users
def load_all_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# Helper to save all users
def save_all_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2)

# Helper to load temp passwords
def load_temp_passwords():
    if not os.path.exists(TEMP_PASSWORDS_FILE):
        return {}
    with open(TEMP_PASSWORDS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# Helper to save temp passwords
def save_temp_passwords(temp_passwords):
    with open(TEMP_PASSWORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(temp_passwords, f, indent=2)

# Register a new user
def register_user(email: str, username: str, password: str) -> Optional[str]:
    email = email.strip().lower()
    users = load_all_users()
    if any(u['email'] == email for u in users):
        return 'Email already registered.'
    if any(u['username'].lower() == username.lower() for u in users):
        return 'Username already taken.'
    if len(password) < 6:
        return 'Password must be at least 6 characters.'
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users.append({
        'email': email,
        'username': username,
        'password_hash': password_hash
    })
    save_all_users(users)
    return None  # Success

# Login user
def login_user(email: str, password: str) -> Optional[dict]:
    email = email.strip().lower()
    users = load_all_users()
    for user in users:
        if user['email'] == email:
            if bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
                return user
            else:
                return None
    return None

# Load user profile by email
def load_user_profile(email: str) -> Optional[dict]:
    users = load_all_users()
    for user in users:
        if user['email'] == email:
            return user
    return None

# Generate and store a temporary password for a user
def set_temp_password(email: str) -> Optional[str]:
    users = load_all_users()
    user = next((u for u in users if u['email'] == email.strip().lower()), None)
    if not user:
        return None
    temp_password = secrets.token_urlsafe(8)
    temp_hash = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()
    expiry = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    temp_passwords = load_temp_passwords()
    temp_passwords[email] = {'hash': temp_hash, 'expires': expiry}
    save_temp_passwords(temp_passwords)
    return temp_password

# Validate a temporary password
def validate_temp_password(email: str, temp_password: str) -> bool:
    temp_passwords = load_temp_passwords()
    entry = temp_passwords.get(email)
    if not entry:
        return False
    if datetime.utcnow() > datetime.fromisoformat(entry['expires']):
        # Expired
        del temp_passwords[email]
        save_temp_passwords(temp_passwords)
        return False
    if bcrypt.checkpw(temp_password.encode(), entry['hash'].encode()):
        # Valid, clear after use
        del temp_passwords[email]
        save_temp_passwords(temp_passwords)
        return True
    return False

# Send temporary password via email
def send_temp_password_email(email: str, temp_password: str) -> bool:
    # SMTP config from environment
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    from_addr = smtp_user
    to_addr = email
    subject = 'Your WizWord Temporary Password'
    body = f"Your temporary password is: {temp_password}\n\nIt will expire in 5 minutes. Please use it to log in and reset your password immediately."
    msg = MIMEText(body)
    msg['Subject'] = subject
    from_email = os.getenv('ADMIN_EMAIL') or smtp_user or ''
    from_name = os.getenv('WIZWORD_FROM_NAME', 'WizWordAi')
    msg['From'] = (f"{from_name} <{from_email}>" if from_email else from_name)
    msg['To'] = to_addr
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send temp password email: {e}")
        return False

# API: Forgot password handler
def forgot_password(email: str) -> Optional[str]:
    temp_password = set_temp_password(email)
    if not temp_password:
        return None
    if send_temp_password_email(email, temp_password):
        return 'Temporary password sent to your email.'
    else:
        return 'Failed to send email. Please try again later.'

# Send share card image as email attachment
def send_share_card_email(email: str, subject: str, body: str, image_path: str) -> bool:
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    from_addr = smtp_user
    to_addr = email
    msg = MIMEMultipart()
    from_email = os.getenv('ADMIN_EMAIL') or smtp_user or ''
    from_name = os.getenv('WIZWORD_FROM_NAME', 'WizWordAi')
    msg['From'] = (f"{from_name} <{from_email}>" if from_email else from_name)
    msg['To'] = to_addr
    msg['Subject'] = subject
    site = os.getenv('WIZWORD_SITE', 'https://wizword.org')
    body_final = f"{body}\n\nVisit <{site}> to view or share your results."
    msg.attach(MIMEText(body_final, 'plain'))
    # Attach image
    try:
        with open(image_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(image_path)}"')
        msg.attach(part)
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            response = server.sendmail(from_addr, [to_addr], msg.as_string())
            
        return True
    except Exception as e:
        import traceback
        print(f"Failed to send share card email: {e}")
        traceback.print_exc()
        return False 