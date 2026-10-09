#!/usr/bin/env python3
"""
LoginTabSystem - Cybersecurity Modal 0 Edition
Modern login system with tab-based authentication
Optimized for Termux (Android Terminal)
"""

import os
import sys
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import secrets
import re
import time
from typing import Dict, Optional, Tuple

# Color codes untuk terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ============================================
# DATABASE SETUP
# ============================================

class Database:
    def __init__(self, db_path: str = "db/users.db"):
        self.db_path = db_path
        Path("db").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Audit log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 2FA table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS two_factor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                secret TEXT NOT NULL,
                is_enabled BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def execute(self, query: str, params: tuple = ()):
        """Execute query that modifies data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        result = cursor.lastrowid
        conn.close()
        return result
    
    def fetch_one(self, query: str, params: tuple = ()):
        """Fetch one row"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result
    
    def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all rows"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results

# ============================================
# SECURITY UTILITIES
# ============================================

class Security:
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        new_hash, _ = Security.hash_password(password, salt)
        return new_hash == password_hash
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password minimal 8 karakter"
        if not re.search(r'[A-Z]', password):
            return False, "Password harus mengandung huruf besar"
        if not re.search(r'[a-z]', password):
            return False, "Password harus mengandung huruf kecil"
        if not re.search(r'[0-9]', password):
            return False, "Password harus mengandung angka"
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            return False, "Password harus mengandung karakter spesial (!@#$%^&*)"
        return True, "Password valid"
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Validate username format"""
        if len(username) < 3:
            return False, "Username minimal 3 karakter"
        if len(username) > 20:
            return False, "Username maksimal 20 karakter"
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username hanya boleh mengandung huruf, angka, underscore, dan dash"
        return True, "Username valid"

# ============================================
# AUDIT LOGGING
# ============================================

class AuditLog:
    def __init__(self, db: Database):
        self.db = db
    
    def log_action(self, user_id: Optional[int], action: str, details: str = "", ip: str = "127.0.0.1"):
        """Log user action"""
        self.db.execute(
            'INSERT INTO audit_log (user_id, action, details, ip_address) VALUES (?, ?, ?, ?)',
            (user_id, action, details, ip)
        )
    
    def get_logs(self, limit: int = 50):
        """Get audit logs"""
        return self.db.fetch_all(
            'SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?',
            (limit,)
        )
    
    def get_user_logs(self, user_id: int, limit: int = 20):
        """Get logs for specific user"""
        return self.db.fetch_all(
            'SELECT * FROM audit_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
            (user_id, limit)
        )

# ============================================
# USER MANAGEMENT
# ============================================

class UserManager:
    def __init__(self, db: Database):
        self.db = db
        self.audit = AuditLog(db)
    
    def register(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """Register new user"""
        # Validate inputs
        valid_username, msg_username = Security.validate_username(username)
        if not valid_username:
            return False, msg_username
        
        if not Security.validate_email(email):
            return False, "Format email tidak valid"
        
        valid_password, msg_password = Security.validate_password(password)
        if not valid_password:
            return False, msg_password
        
        # Check if user exists
        existing = self.db.fetch_one(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        )
        if existing:
            return False, "Username atau email sudah terdaftar"
        
        # Hash password
        password_hash, salt = Security.hash_password(password)
        
        # Insert user
        try:
            user_id = self.db.execute(
                'INSERT INTO users (username, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)',
                (username, email, password_hash, salt, 'user')
            )
            
            # Create 2FA record
            secret = Security.generate_token()
            self.db.execute(
                'INSERT INTO two_factor (user_id, secret, is_enabled) VALUES (?, ?, ?)',
                (user_id, secret, 0)
            )
            
            self.audit.log_action(user_id, 'REGISTER', f'User baru terdaftar: {username}')
            return True, "Registrasi berhasil!"
        except Exception as e:
            return False, f"Error registrasi: {str(e)}"
    
    def login(self, username: str, password: str, ip: str = "127.0.0.1") -> Tuple[bool, str, Optional[int]]:
        """Login user"""
        user = self.db.fetch_one(
            'SELECT id, password_hash, salt, is_active, locked_until, failed_attempts FROM users WHERE username = ?',
            (username,)
        )
        
        if not user:
            self.audit.log_action(None, 'LOGIN_FAILED', f'User tidak ditemukan: {username}', ip)
            return False, "Username atau password salah", None
        
        # Check if account is locked
        if user['locked_until']:
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < locked_until:
                remaining = (locked_until - datetime.now()).seconds // 60
                self.audit.log_action(user['id'], 'LOGIN_LOCKED', f'Akun terkunci, sisa {remaining} menit', ip)
                return False, f"Akun terkunci. Coba lagi dalam {remaining} menit", None
            else:
                # Unlock account
                self.db.execute(
                    'UPDATE users SET locked_until = NULL, failed_attempts = 0 WHERE id = ?',
                    (user['id'],)
                )
        
        # Verify password
        if not Security.verify_password(password, user['password_hash'], user['salt']):
            failed_attempts = user['failed_attempts'] + 1
            
            if failed_attempts >= 5:
                locked_until = datetime.now() + timedelta(minutes=15)
                self.db.execute(
                    'UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?',
                    (failed_attempts, locked_until.isoformat(), user['id'])
                )
                self.audit.log_action(user['id'], 'LOGIN_FAILED', 'Akun dikunci karena gagal login 5x', ip)
                return False, "Terlalu banyak percobaan login gagal. Akun terkunci 15 menit", None
            else:
                self.db.execute(
                    'UPDATE users SET failed_attempts = ? WHERE id = ?',
                    (failed_attempts, user['id'])
                )
                self.audit.log_action(user['id'], 'LOGIN_FAILED', f'Percobaan ke-{failed_attempts}', ip)
                return False, "Username atau password salah", None
        
        if not user['is_active']:
            return False, "Akun tidak aktif", None
        
        # Login successful
        token = Security.generate_token()
        expires_at = datetime.now() + timedelta(hours=24)
        
        self.db.execute(
            'INSERT INTO sessions (user_id, token, ip_address, expires_at) VALUES (?, ?, ?, ?)',
            (user['id'], token, ip, expires_at.isoformat())
        )
        
        self.db.execute(
            'UPDATE users SET last_login = ?, failed_attempts = 0, locked_until = NULL WHERE id = ?',
            (datetime.now().isoformat(), user['id'])
        )
        
        self.audit.log_action(user['id'], 'LOGIN_SUCCESS', f'Login berhasil dari {ip}', ip)
        return True, "Login berhasil!", user['id']
    
    def get_user(self, user_id: int):
        """Get user data"""
        return self.db.fetch_one(
            'SELECT id, username, email, role, is_active, created_at, last_login FROM users WHERE id = ?',
            (user_id,)
        )
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        user = self.db.fetch_one(
            'SELECT password_hash, salt FROM users WHERE id = ?',
            (user_id,)
        )
        
        if not user:
            return False, "User tidak ditemukan"
        
        # Verify old password
        if not Security.verify_password(old_password, user['password_hash'], user['salt']):
            return False, "Password lama tidak sesuai"
        
        # Validate new password
        valid, msg = Security.validate_password(new_password)
        if not valid:
            return False, msg
        
        # Hash new password
        password_hash, salt = Security.hash_password(new_password)
        
        self.db.execute(
            'UPDATE users SET password_hash = ?, salt = ?, updated_at = ? WHERE id = ?',
            (password_hash, salt, datetime.now().isoformat(), user_id)
        )
        
        self.audit.log_action(user_id, 'PASSWORD_CHANGED', 'User mengubah password')
        return True, "Password berhasil diubah"
    
    def list_users(self) -> list:
        """List all users (admin only)"""
        return self.db.fetch_all(
            'SELECT id, username, email, role, is_active, created_at, last_login FROM users ORDER BY created_at DESC'
        )

# ============================================
# CLI INTERFACE
# ============================================

class LoginSystem:
    def __init__(self):
        self.db = Database()
        self.user_manager = UserManager(self.db)
        self.audit = AuditLog(self.db)
        self.current_user_id = None
        self.current_username = None
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}╔{'═' * 50}╗{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}║ {title.center(48)} ║{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}╚{'═' * 50}╝{Colors.ENDC}\n")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")
    
    def menu_main(self):
        """Main menu"""
        while True:
            self.clear_screen()
            self.print_header("CYBERSECURITY LOGIN SYSTEM")
            print(f"{Colors.BOLD}Modal 0 Edition - Termux Compatible{Colors.ENDC}")
            print()
            
            if self.current_user_id:
                print(f"{Colors.OKGREEN}Status: Logged in as {self.current_username}{Colors.ENDC}\n")
                print("[1] Dashboard")
                print("[2] Change Password")
                print("[3] View Profile")
                print("[4] Logout")
                print("[5] Admin Panel")
                print("[6] Exit")
            else:
                print(f"{Colors.OKCYAN}Status: Not logged in{Colors.ENDC}\n")
                print("[1] Login")
                print("[2] Register")
                print("[3] Audit Log")
                print("[4] Exit")
            
            print()
            choice = input(f"{Colors.BOLD}Pilih menu [{Colors.OKBLUE}1-{4 if not self.current_user_id else 6}{Colors.BOLD}]: {Colors.ENDC}").strip()
            
            if not self.current_user_id:
                if choice == '1':
                    self.menu_login()
                elif choice == '2':
                    self.menu_register()
                elif choice == '3':
                    self.menu_audit_log()
                elif choice == '4':
                    print(f"\n{Colors.OKGREEN}Terima kasih! Goodbye...{Colors.ENDC}\n")
                    sys.exit(0)
                else:
                    self.print_error("Pilihan tidak valid")
                    time.sleep(1)
            else:
                if choice == '1':
                    self.menu_dashboard()
                elif choice == '2':
                    self.menu_change_password()
                elif choice == '3':
                    self.menu_profile()
                elif choice == '4':
                    self.logout()
                elif choice == '5':
                    self.menu_admin()
                elif choice == '6':
                    self.logout()
                    print(f"\n{Colors.OKGREEN}Goodbye!{Colors.ENDC}\n")
                    sys.exit(0)
                else:
                    self.print_error("Pilihan tidak valid")
                    time.sleep(1)
    
    def menu_login(self):
        """Login menu"""
        self.clear_screen()
        self.print_header("LOGIN")
        
        username = input(f"{Colors.BOLD}Username: {Colors.ENDC}").strip()
        password = input(f"{Colors.BOLD}Password: {Colors.ENDC}").strip()
        
        success, message, user_id = self.user_manager.login(username, password)
        
        if success:
            self.current_user_id = user_id
            self.current_username = username
            self.print_success(message)
        else:
            self.print_error(message)
        
        time.sleep(2)
    
    def menu_register(self):
        """Register menu"""
        self.clear_screen()
        self.print_header("REGISTER")
        
        username = input(f"{Colors.BOLD}Username: {Colors.ENDC}").strip()
        email = input(f"{Colors.BOLD}Email: {Colors.ENDC}").strip()
        password = input(f"{Colors.BOLD}Password (min 8 karakter, uppercase, lowercase, angka, spesial): {Colors.ENDC}").strip()
        password_confirm = input(f"{Colors.BOLD}Confirm Password: {Colors.ENDC}").strip()
        
        if password != password_confirm:
            self.print_error("Password tidak cocok")
            time.sleep(2)
            return
        
        success, message = self.user_manager.register(username, email, password)
        
        if success:
            self.print_success(message)
        else:
            self.print_error(message)
        
        time.sleep(2)
    
    def menu_dashboard(self):
        """User dashboard"""
        self.clear_screen()
        self.print_header(f"DASHBOARD - {self.current_username.upper()}")
        
        user = self.user_manager.get_user(self.current_user_id)
        if user:
            print(f"Username: {Colors.OKBLUE}{user['username']}{Colors.ENDC}")
            print(f"Email: {Colors.OKBLUE}{user['email']}{Colors.ENDC}")
            print(f"Role: {Colors.OKCYAN}{user['role']}{Colors.ENDC}")
            print(f"Joined: {Colors.OKCYAN}{user['created_at']}{Colors.ENDC}")
            print(f"Last Login: {Colors.OKCYAN}{user['last_login']}{Colors.ENDC}")
            
            # Recent activity
            print(f"\n{Colors.BOLD}Recent Activity:{Colors.ENDC}")
            logs = self.audit.get_user_logs(self.current_user_id, 5)
            for log in logs:
                print(f"  • {log['action']} - {log['details']} ({log['timestamp']})")
        
        print()
        input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
    
    def menu_profile(self):
        """View profile"""
        self.clear_screen()
        self.print_header("PROFILE")
        
        user = self.user_manager.get_user(self.current_user_id)
        if user:
            print(f"ID: {Colors.OKBLUE}{user['id']}{Colors.ENDC}")
            print(f"Username: {Colors.OKBLUE}{user['username']}{Colors.ENDC}")
            print(f"Email: {Colors.OKBLUE}{user['email']}{Colors.ENDC}")
            print(f"Role: {Colors.OKCYAN}{user['role']}{Colors.ENDC}")
            print(f"Active: {Colors.OKGREEN}Yes{Colors.ENDC if user['is_active'] else Colors.FAIL}No{Colors.ENDC}")
            print(f"Created: {Colors.OKCYAN}{user['created_at']}{Colors.ENDC}")
            print(f"Last Updated: {Colors.OKCYAN}{user['last_login']}{Colors.ENDC}")
        
        print()
        input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
    
    def menu_change_password(self):
        """Change password menu"""
        self.clear_screen()
        self.print_header("CHANGE PASSWORD")
        
        old_password = input(f"{Colors.BOLD}Old Password: {Colors.ENDC}").strip()
        new_password = input(f"{Colors.BOLD}New Password: {Colors.ENDC}").strip()
        new_password_confirm = input(f"{Colors.BOLD}Confirm New Password: {Colors.ENDC}").strip()
        
        if new_password != new_password_confirm:
            self.print_error("Password baru tidak cocok")
            time.sleep(2)
            return
        
        success, message = self.user_manager.change_password(self.current_user_id, old_password, new_password)
        
        if success:
            self.print_success(message)
        else:
            self.print_error(message)
        
        time.sleep(2)
    
    def menu_audit_log(self):
        """View audit log"""
        self.clear_screen()
        self.print_header("AUDIT LOG")
        
        logs = self.audit.get_logs(20)
        if logs:
            for log in logs:
                user_info = f"User ID: {log['user_id']}" if log['user_id'] else "System"
                print(f"{Colors.OKCYAN}[{log['timestamp']}]{Colors.ENDC}")
                print(f"  Action: {Colors.BOLD}{log['action']}{Colors.ENDC}")
                print(f"  {user_info}")
                print(f"  Details: {log['details']}")
                print(f"  IP: {log['ip_address']}")
                print()
        else:
            self.print_info("Belum ada audit log")
        
        print()
        input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
    
    def menu_admin(self):
        """Admin panel"""
        self.clear_screen()
        self.print_header("ADMIN PANEL")
        
        user = self.user_manager.get_user(self.current_user_id)
        if not user or user['role'] != 'admin':
            self.print_error("Anda tidak memiliki akses admin")
            time.sleep(2)
            return
        
        print("[1] List All Users")
        print("[2] View All Audit Logs")
        print("[3] Back")
        print()
        
        choice = input(f"{Colors.BOLD}Pilih [{Colors.OKBLUE}1-3{Colors.BOLD}]: {Colors.ENDC}").strip()
        
        if choice == '1':
            self.clear_screen()
            self.print_header("ALL USERS")
            users = self.user_manager.list_users()
            if users:
                print(f"{Colors.BOLD}{'ID':<5} {'Username':<15} {'Email':<25} {'Role':<10} {'Active':<7}{Colors.ENDC}")
                print("─" * 70)
                for u in users:
                    active = "Yes" if u['is_active'] else "No"
                    print(f"{u['id']:<5} {u['username']:<15} {u['email']:<25} {u['role']:<10} {active:<7}")
            else:
                self.print_info("Belum ada users")
            print()
            input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '2':
            self.menu_audit_log()
    
    def logout(self):
        """Logout user"""
        self.audit.log_action(self.current_user_id, 'LOGOUT', 'User logout')
        self.current_user_id = None
        self.current_username = None
        self.print_success("Logout berhasil")
        time.sleep(1)

# ============================================
# MAIN
# ============================================

def main():
    """Main entry point"""
    try:
        system = LoginSystem()
        
        # Initialize with demo users if database is empty
        users = system.db.fetch_all('SELECT COUNT(*) as count FROM users')
        if users[0]['count'] == 0:
            print(f"{Colors.OKBLUE}Initializing system with demo users...{Colors.ENDC}")
            
            # Create admin user
            system.user_manager.register('admin', 'admin@localhost', 'Admin@123456')
            
            # Create demo user
            system.user_manager.register('demo', 'demo@localhost', 'Demo@123456')
            
            print(f"{Colors.OKGREEN}Demo users created!{Colors.ENDC}")
            print(f"{Colors.WARNING}Admin credentials: admin / Admin@123456{Colors.ENDC}")
            print(f"{Colors.WARNING}Demo credentials: demo / Demo@123456{Colors.ENDC}")
            time.sleep(3)
        
        system.menu_main()
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Program interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {str(e)}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
