#!/usr/bin/env python3
"""
Setup script for LoginTabSystem
Initialize database and create admin user
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import Database, UserManager, Colors
import time

def setup():
    """Run setup"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}═══════════════════════════════════════════{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  CYBERSECURITY LOGIN SYSTEM - SETUP{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}═══════════════════════════════════════════{Colors.ENDC}\n")
    
    print(f"{Colors.OKCYAN}Creating database structure...{Colors.ENDC}")
    db = Database()
    print(f"{Colors.OKGREEN}✓ Database initialized{Colors.ENDC}")
    
    user_manager = UserManager(db)
    
    # Check if users already exist
    existing_users = db.fetch_all('SELECT COUNT(*) as count FROM users')
    if existing_users[0]['count'] > 0:
        print(f"\n{Colors.WARNING}Database already has users!{Colors.ENDC}")
        response = input(f"{Colors.BOLD}Reset database? (y/n): {Colors.ENDC}").strip().lower()
        
        if response == 'y':
            print(f"{Colors.WARNING}Resetting database...{Colors.ENDC}")
            db.execute('DELETE FROM sessions')
            db.execute('DELETE FROM audit_log')
            db.execute('DELETE FROM two_factor')
            db.execute('DELETE FROM users')
            print(f"{Colors.OKGREEN}✓ Database reset{Colors.ENDC}")
        else:
            print(f"{Colors.OKCYAN}Keeping existing data{Colors.ENDC}")
            return
    
    print(f"\n{Colors.OKCYAN}Creating default users...{Colors.ENDC}")
    
    # Create admin user
    print(f"\n{Colors.BOLD}Admin User:{Colors.ENDC}")
    username = 'admin'
    email = 'admin@localhost'
    password = 'Admin@123456'
    
    success, message = user_manager.register(username, email, password)
    if success:
        print(f"{Colors.OKGREEN}✓ Admin user created{Colors.ENDC}")
        print(f"  Username: {Colors.OKBLUE}{username}{Colors.ENDC}")
        print(f"  Password: {Colors.OKBLUE}{password}{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")
    
    # Create demo user
    print(f"\n{Colors.BOLD}Demo User:{Colors.ENDC}")
    username = 'demo'
    email = 'demo@localhost'
    password = 'Demo@123456'
    
    success, message = user_manager.register(username, email, password)
    if success:
        print(f"{Colors.OKGREEN}✓ Demo user created{Colors.ENDC}")
        print(f"  Username: {Colors.OKBLUE}{username}{Colors.ENDC}")
        print(f"  Password: {Colors.OKBLUE}{password}{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}═══════════════════════════════════════════{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{Colors.BOLD}  Setup Complete!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{Colors.BOLD}═══════════════════════════════════════════{Colors.ENDC}")
    print(f"\n{Colors.OKCYAN}Next step: Run 'python3 main.py'{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        setup()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Setup interrupted{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Setup error: {str(e)}{Colors.ENDC}")
        sys.exit(1)
