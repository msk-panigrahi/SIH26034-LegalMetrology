"""
Script to create an admin user.

Usage:
    python -m app.create_admin
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.auth.password import hash_password


def create_admin():
    """Interactive script to create an admin user."""
    print("=" * 50)
    print("Create Admin User")
    print("=" * 50)

    full_name = input("Full name: ").strip()
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()

    if not all([full_name, username, email, password]):
        print("Error: All fields are required.")
        return

    if len(password) < 6:
        print("Error: Password must be at least 6 characters.")
        return

    db = SessionLocal()
    try:
        # Check if username or email exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            print("Error: Username or email already exists.")
            return

        admin = User(
            full_name=full_name,
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="ADMIN",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"\nAdmin user created successfully: {username}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
