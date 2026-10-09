#!/usr/bin/env python3
"""
LoginTabSystem - Cybersecurity Modal 1 Edition (Enhanced)
Modern login system with tab-based authentication + Beautiful UI
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
import threading

# Color codes untuk terminal dengan gradasi
class Colors:
    # Basic Colors
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # Bright Colors
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_RED = '\033[91m'
    
    # Background
    BG_DARK = '\033[40m'
    BG_BLUE = '\033[44m'
    
    # Additional Effects
    DIM = '\033[2m'
    BLINK = '\033[5m'

# ============================================
# ANIMATION & EFFECTS
# ============================================

class Effects:
    @staticmethod
    def loading_animation(duration: float = 2, message: str = "Processing"):
        """Animated loading bar"""
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        end_time = time.time() + duration
        
        while time.time() < end_time:
            for frame in frames:
                remaining = end_time - time.time()
                if remaining <= 0:
                    break
                sys.stdout.write(f'\r{Colors.OKBLUE}{frame} {message}...{Colors.ENDC}')
                sys.stdout.flush()
                time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()
    
    @staticmethod
    def progress_bar(current: int, total: int, width: int = 30):
        """Display progress bar"""
        percent = current / total
        filled = int(width * percent)
        bar = '█' * filled + '░' * (width - filled)
        print(f'\r{Colors.OKGREEN}[{bar}] {int(percent * 100)}%{Colors.ENDC}', end='', flush=True)
    
    @staticmethod
    def typing_effect(text: str, speed: float = 0.02):
        """Typing animation effect"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(speed)
        print()
    
    @staticmethod
    def fade_in_text(text: str, color: str = Colors.HEADER):
        """Fade in effect with color"""
        print(f"{color}{text}{Colors.ENDC}")
    
    @staticmethod
    def print_box(title: str, content: list, width: int = 60, color: str = Colors.HEADER):
        """Print beautiful box with content"""
        print(f"\n{color}╔{'═' * (width - 2)}╗{Colors.ENDC}")
        print(f"{color}║ {title.center(width - 4)} ║{Colors.ENDC}")
        print(f"{color}╠{'═' * (width - 2)}╣{Colors.ENDC}")
        
        for line in content:
            if len(line) < width - 4:
                padding = width - 4 - len(line)
                print(f"{color}║{Colors.ENDC} {line}{' ' * padding} {color}║{Colors.ENDC}")
            else:
                print(f"{color}║{Colors.ENDC} {line[:width-5]}{color}║{Colors.ENDC}")
        
        print(f"{color}╚{'═' * (width - 2)}╝{Colors.ENDC}\n")
    
    @staticmethod
    def print_table(headers: list, rows: list):
        """Print formatted table"""
        if not rows:
            print(f"{Colors.WARNING}No data to display{Colors.ENDC}")
            return
        
        # Calculate column widths
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Header
        header_row = " │ ".join(f"{Colors.BOLD}{h:<{w}}{Colors.ENDC}" for h, w in zip(headers, col_widths))
        print(f"\n {header_row}")
        print(" " + "─┼─".join("─" * w for w in col_widths))
        
        # Rows
        for i, row in enumerate(rows):
            row_str = " │ ".join(f"{str(cell):<{w}}" for cell, w in zip(row, col_widths))
            color = Colors.OKGREEN if i % 2 == 0 else Colors.OKCYAN
            print(f" {color}{row_str}{Colors.ENDC}")
        print()

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
                locked_until TIMESTAMP,
                avatar_color TEXT DEFAULT '🟦'
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
        """Login user with animated progress"""
        user = self.db.fetch_one(
            'SELECT id, password_hash, salt, is_active, locked_until, failed_attempts FROM users WHERE username = ?',
            (username,)
        )
        
        if not user:
            self.audit.log_action(None, 'LOGIN_FAILED', f'User tidak ditemukan: {username}', ip)
            return False, "Username atau password salah", None
        
        # Show progress
        Effects.progress_bar(25, 100)
        time.sleep(0.3)
        
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
        
        Effects.progress_bar(50, 100)
        time.sleep(0.3)
        
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
        
        Effects.progress_bar(75, 100)
        time.sleep(0.3)
        
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
        
        Effects.progress_bar(100, 100)
        print()
        
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
    
    def get_user_stats(self) -> dict:
        """Get user statistics"""
        total = self.db.fetch_one('SELECT COUNT(*) as count FROM users')
        admins = self.db.fetch_one('SELECT COUNT(*) as count FROM users WHERE role = "admin"')
        active = self.db.fetch_one('SELECT COUNT(*) as count FROM users WHERE is_active = 1')
        
        return {
            'total': total['count'] if total else 0,
            'admins': admins['count'] if admins else 0,
            'active': active['count'] if active else 0
        }

# ============================================
# CLI INTERFACE - ENHANCED
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
    
    def print_header(self, title: str, subtitle: str = ""):
        """Print animated header"""
        width = 60
        print(f"\n{Colors.HEADER}{Colors.BOLD}╔{'═' * (width - 2)}╗{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}║ {title.center(width - 4)} ║{Colors.ENDC}")
        if subtitle:
            print(f"{Colors.OKCYAN}{Colors.BOLD}║ {subtitle.center(width - 4)} ║{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}╚{'═' * (width - 2)}╝{Colors.ENDC}\n")
    
    def print_success(self, message: str):
        """Print success message with animation"""
        print(f"{Colors.OKGREEN}{'✓' * 2} {message}{Colors.ENDC}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.FAIL}{'✗' * 2} {message}{Colors.ENDC}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")
    
    def print_divider(self, char: str = "─"):
        """Print decorative divider"""
        print(f"{Colors.DIM}{char * 60}{Colors.ENDC}")
    
    def menu_main(self):
        """Main menu with enhanced UI"""
        while True:
            self.clear_screen()
            self.print_header("🔐 CYBERSECURITY LOGIN SYSTEM", "Modal 1 Edition - Enhanced UI")
            
            if self.current_user_id:
                user = self.user_manager.get_user(self.current_user_id)
                status_color = Colors.OKGREEN if user['role'] == 'admin' else Colors.OKCYAN
                role_badge = f"[{user['role'].upper()}]"
                
                print(f"{status_color}👤 Logged in as: {Colors.BOLD}{self.current_username}{Colors.ENDC} {role_badge}\n")
                print(f"{Colors.BOLD}Dashboard:{Colors.ENDC}")
                print(f"  {Colors.OKBLUE}[1]{Colors.ENDC}  Dashboard")
                print(f"  {Colors.OKBLUE}[2]{Colors.ENDC}  Change Password")
                print(f"  {Colors.OKBLUE}[3]{Colors.ENDC}  View Profile")
                print(f"  {Colors.OKBLUE}[4]{Colors.ENDC}  Activity Log")
                if user['role'] == 'admin':
                    print(f"\n{Colors.BOLD}Admin Tools:{Colors.ENDC}")
                    print(f"  {Colors.WARNING}[5]{Colors.ENDC}  Admin Panel")
                print(f"\n{Colors.BOLD}Account:{Colors.ENDC}")
                print(f"  {Colors.FAIL}[6]{Colors.ENDC}  Logout")
                print(f"  {Colors.FAIL}[0]{Colors.ENDC}  Exit")
            else:
                print(f"{Colors.WARNING}Status: Not logged in{Colors.ENDC}\n")
                print(f"{Colors.BOLD}Authentication:{Colors.ENDC}")
                print(f"  {Colors.OKGREEN}[1]{Colors.ENDC}  Login")
                print(f"  {Colors.OKGREEN}[2]{Colors.ENDC}  Register")
                print(f"\n{Colors.BOLD}Info:{Colors.ENDC}")
                print(f"  {Colors.OKCYAN}[3]{Colors.ENDC}  Audit Log")
                print(f"  {Colors.FAIL}[0]{Colors.ENDC}  Exit")
            
            self.print_divider()
            
            max_choice = 6 if self.current_user_id else 3
            choice = input(f"{Colors.BOLD}Pilih menu [{Colors.OKBLUE}0-{max_choice}{Colors.BOLD}]: {Colors.ENDC}").strip()
            
            if not self.current_user_id:
                if choice == '1':
                    self.menu_login()
                elif choice == '2':
                    self.menu_register()
                elif choice == '3':
                    self.menu_audit_log()
                elif choice == '0':
                    self.menu_exit()
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
                    self.menu_activity()
                elif choice == '5':
                    self.menu_admin()
                elif choice == '6':
                    self.logout()
                elif choice == '0':
                    self.logout()
                    self.menu_exit()
                else:
                    self.print_error("Pilihan tidak valid")
                    time.sleep(1)
    
    def menu_login(self):
        """Login menu with animation"""
        self.clear_screen()
        self.print_header("🔑 LOGIN", "Enter your credentials")
        
        username = input(f"{Colors.BOLD}└─ Username: {Colors.ENDC}").strip()
        password = input(f"{Colors.BOLD}└─ Password: {Colors.ENDC}").strip()
        
        print()
        Effects.loading_animation(2, "Verifying credentials")
        
        success, message, user_id = self.user_manager.login(username, password)
        
        if success:
            self.current_user_id = user_id
            self.current_username = username
            self.print_success(message)
            Effects.loading_animation(1.5, "Loading dashboard")
        else:
            self.print_error(message)
        
        time.sleep(1)
    
    def menu_register(self):
        """Register menu with better formatting"""
        self.clear_screen()
        self.print_header("📝 REGISTER", "Create a new account")
        
        print(f"{Colors.DIM}Password requirements:{Colors.ENDC}")
        print(f"  • Minimum 8 karakter")
        print(f"  • Huruf besar (A-Z)")
        print(f"  • Huruf kecil (a-z)")
        print(f"  • Angka (0-9)")
        print(f"  • Karakter spesial (!@#$%^&*)\n")
        
        username = input(f"{Colors.BOLD}└─ Username: {Colors.ENDC}").strip()
        email = input(f"{Colors.BOLD}└─ Email: {Colors.ENDC}").strip()
        password = input(f"{Colors.BOLD}└─ Password: {Colors.ENDC}").strip()
        password_confirm = input(f"{Colors.BOLD}└─ Confirm Password: {Colors.ENDC}").strip()
        
        if password != password_confirm:
            self.print_error("Password tidak cocok")
            time.sleep(2)
            return
        
        print()
        Effects.loading_animation(2, "Creating account")
        
        success, message = self.user_manager.register(username, email, password)
        
        if success:
            self.print_success(message)
            self.print_info("Anda sekarang dapat login")
        else:
            self.print_error(message)
        
        time.sleep(2)
    
    def menu_dashboard(self):
        """Enhanced dashboard"""
        self.clear_screen()
        self.print_header(f"📊 DASHBOARD", f"Welcome {self.current_username}!")
        
        user = self.user_manager.get_user(self.current_user_id)
        if user:
            # User Info Box
            content = [
                f"Username: {Colors.OKBLUE}{user['username']}{Colors.ENDC}",
                f"Email: {Colors.OKBLUE}{user['email']}{Colors.ENDC}",
                f"Role: {Colors.OKCYAN}{user['role'].upper()}{Colors.ENDC}",
                f"Status: {Colors.OKGREEN}Active{Colors.ENDC}",
                f"Joined: {user['created_at'][:10]}",
            ]
            
            if user['last_login']:
                content.append(f"Last Login: {user['last_login']}")
            
            Effects.print_box("PROFILE INFORMATION", content, width=60)
            
            # Recent activity
            print(f"{Colors.BOLD}📋 Recent Activity:{Colors.ENDC}")
            logs = self.audit.get_user_logs(self.current_user_id, 5)
            if logs:
                for i, log in enumerate(logs, 1):
                    action_color = Colors.OKGREEN if 'SUCCESS' in log['action'] else Colors.WARNING if 'FAILED' in log['action'] else Colors.OKCYAN
                    print(f"  {i}. {action_color}{log['action']}{Colors.ENDC}")
                    print(f"     → {log['details']}")
                    print(f"     🕐 {log['timestamp']}\n")
            else:
                self.print_info("Belum ada aktivitas")
        
        print()
        input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
    
    def menu_profile(self):
        """View profile with enhanced display"""
        self.clear_screen()
        self.print_header("👤 PROFILE", "User Information")
        
        user = self.user_manager.get_user(self.current_user_id)
        if user:
            profile_data = [
                f"ID: {Colors.OKBLUE}#{user['id']}{Colors.ENDC}",
                f"Username: {Colors.OKBLUE}{user['username']}{Colors.ENDC}",
                f"Email: {Colors.OKBLUE}{user['email']}{Colors.ENDC}",
                f"Role: {Colors.OKCYAN}{user['role'].upper()}{Colors.ENDC}",
                f"Status: {Colors.OKGREEN}Active{Colors.ENDC}",
                f"Member Since: {user['created_at'][:10]}",
                f"Last Activity: {user['last_login'] if user['last_login'] else 'Never'}"
            ]
            
            Effects.print_box("YOUR PROFILE", profile_data, width=60, color=Colors.OKGREEN)
        
        input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
    
    def menu_activity(self):
        """View user activity log"""
        self.clear_screen()
        self.print_header("📝 ACTIVITY LOG", "Your Recent Actions")
        
        logs = self.audit.get_user_logs(self.current_user_id, 15)
        if logs:
            for i, log in enumerate(logs, 1):
                action_color = Colors.OKGREEN if 'SUCCESS' in log['action'] else Colors.FAIL if 'FAILED' in log['action'] else Colors.OKCYAN
                print(f"{i:2}. {action_color}{log['action']:<15}{Colors.ENDC} │ {log['details']}")
                print(f"    └─ {Colors.DIM}{log['timestamp']} from {log['ip_address']}{Colors.ENDC}\n")
        else:
            self.print_info("Belum ada aktivitas tercatat")
        
        input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
    
    def menu_change_password(self):
        """Change password with validation"""
        self.clear_screen()
        self.print_header("🔐 CHANGE PASSWORD", "Update your password")
        
        old_password = input(f"{Colors.BOLD}Old Password: {Colors.ENDC}").strip()
        print()
        new_password = input(f"{Colors.BOLD}New Password: {Colors.ENDC}").strip()
        new_password_confirm = input(f"{Colors.BOLD}Confirm Password: {Colors.ENDC}").strip()
        
        if new_password != new_password_confirm:
            self.print_error("Password baru tidak cocok")
            time.sleep(2)
            return
        
        print()
        Effects.loading_animation(1.5, "Validating and updating")
        
        success, message = self.user_manager.change_password(self.current_user_id, old_password, new_password)
        
        if success:
            self.print_success(message)
        else:
            self.print_error(message)
        
        time.sleep(2)
    
    def menu_audit_log(self):
        """View system audit log"""
        self.clear_screen()
        self.print_header("📊 AUDIT LOG", "System Activity")
        
        logs = self.audit.get_logs(30)
        if logs:
            for i, log in enumerate(logs, 1):
                user_info = f"User#{log['user_id']}" if log['user_id'] else "SYSTEM"
                action_color = Colors.OKGREEN if 'SUCCESS' in log['action'] else Colors.FAIL if 'FAILED' in log['action'] else Colors.WARNING
                
                print(f"{i:2}. {action_color}[{log['action']}]{Colors.ENDC} by {Colors.OKCYAN}{user_info}{Colors.ENDC}")
                print(f"    └─ {log['details']}")
                print(f"    └─ {Colors.DIM}{log['timestamp']} | IP: {log['ip_address']}{Colors.ENDC}\n")
        else:
            self.print_info("Belum ada audit log")
        
        input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
    
    def menu_admin(self):
        """Enhanced admin panel"""
        self.clear_screen()
        self.print_header("⚙️  ADMIN PANEL", "System Administration")
        
        user = self.user_manager.get_user(self.current_user_id)
        if not user or user['role'] != 'admin':
            self.print_error("Anda tidak memiliki akses admin")
            time.sleep(2)
            return
        
        # Admin Statistics
        stats = self.user_manager.get_user_stats()
        print(f"{Colors.BOLD}📊 System Statistics:{Colors.ENDC}")
        print(f"  • Total Users: {Colors.OKGREEN}{stats['total']}{Colors.ENDC}")
        print(f"  • Admin Accounts: {Colors.WARNING}{stats['admins']}{Colors.ENDC}")
        print(f"  • Active Users: {Colors.OKBLUE}{stats['active']}{Colors.ENDC}")
        print()
        
        print(f"{Colors.BOLD}Admin Options:{Colors.ENDC}")
        print(f"  {Colors.OKBLUE}[1]{Colors.ENDC}  List All Users")
        print(f"  {Colors.OKBLUE}[2]{Colors.ENDC}  View All Audit Logs")
        print(f"  {Colors.OKBLUE}[3]{Colors.ENDC}  Back")
        print()
        
        choice = input(f"{Colors.BOLD}Pilih [{Colors.OKBLUE}1-3{Colors.BOLD}]: {Colors.ENDC}").strip()
        
        if choice == '1':
            self.admin_list_users()
        elif choice == '2':
            self.admin_view_logs()
    
    def admin_list_users(self):
        """List all users with nice table"""
        self.clear_screen()
        self.print_header("👥 ALL USERS", "User Management")
        
        users = self.user_manager.list_users()
        if users:
            headers = ["ID", "Username", "Email", "Role", "Status", "Joined"]
            rows = []
            for u in users:
                status = f"{Colors.OKGREEN}✓{Colors.ENDC}" if u['is_active'] else f"{Colors.FAIL}✗{Colors.ENDC}"
                joined = u['created_at'][:10] if u['created_at'] else "N/A"
                rows.append([u['id'], u['username'], u['email'], u['role'].upper(), status, joined])
            
            Effects.print_table(headers, rows)
        else:
            self.print_info("Belum ada users")
        
        input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
    
    def admin_view_logs(self):
        """View all audit logs"""
        self.clear_screen()
        self.print_header("📋 ALL AUDIT LOGS", "System Activity")
        
        logs = self.audit.get_logs(50)
        if logs:
            for i, log in enumerate(logs, 1):
                user_info = f"User#{log['user_id']}" if log['user_id'] else "SYSTEM"
                action_color = Colors.OKGREEN if 'SUCCESS' in log['action'] else Colors.FAIL if 'FAILED' in log['action'] else Colors.WARNING
                
                print(f"{i:2}. {action_color}[{log['action']}]{Colors.ENDC} | {user_info}")
                print(f"    └─ {log['details']}")
                print(f"    └─ {log['timestamp']} | {log['ip_address']}\n")
        else:
            self.print_info("Belum ada audit log")
        
        input(f"{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")
    
    def logout(self):
        """Logout user"""
        self.audit.log_action(self.current_user_id, 'LOGOUT', f'User {self.current_username} logout')
        print()
        Effects.loading_animation(1, "Logging out")
        print()
        self.print_success(f"Goodbye {self.current_username}!")
        self.current_user_id = None
        self.current_username = None
        time.sleep(1)
    
    def menu_exit(self):
        """Exit menu"""
        self.clear_screen()
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}╔════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}║{Colors.ENDC}  Thank you for using LoginTabSystem!                  {Colors.OKGREEN}{Colors.BOLD}║{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}║{Colors.ENDC}  Stay secure and stay safe!                            {Colors.OKGREEN}{Colors.BOLD}║{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}╚════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        sys.exit(0)

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
            system.clear_screen()
            print(f"{Colors.OKBLUE}{Colors.BOLD}╔════════════════════════════════════════════════════════╗{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{Colors.BOLD}║{Colors.ENDC}  🚀 Initializing LoginTabSystem...                     {Colors.OKBLUE}{Colors.BOLD}║{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{Colors.BOLD}╚════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
            
            Effects.loading_animation(2, "Creating demo users")
            
            # Create admin user
            system.user_manager.register('admin', 'admin@localhost', 'Admin@123456')
            Effects.progress_bar(50, 100)
            
            # Create demo user
            system.user_manager.register('demo', 'demo@localhost', 'Demo@123456')
            Effects.progress_bar(100, 100)
            print()
            
            print(f"{Colors.OKGREEN}✓ Demo users created!{Colors.ENDC}")
            print(f"{Colors.WARNING}Admin credentials: {Colors.BOLD}admin{Colors.ENDC}{Colors.WARNING} / {Colors.BOLD}Admin@123456{Colors.ENDC}")
            print(f"{Colors.WARNING}Demo credentials:  {Colors.BOLD}demo{Colors.ENDC}{Colors.WARNING} / {Colors.BOLD}Demo@123456{Colors.ENDC}\n")
            time.sleep(3)
        
        system.menu_main()
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Program interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
