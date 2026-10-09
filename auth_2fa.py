#!/usr/bin/env python3
"""
Two-Factor Authentication Module
Mendukung TOTP (Time-based One-Time Password) dan Email OTP
"""

import secrets
import time
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Tuple, Optional
import json

class TOTP:
    """Time-based One-Time Password (Google Authenticator compatible)"""
    
    @staticmethod
    def generate_secret(length: int = 32) -> str:
        """Generate secret key untuk TOTP"""
        return base64.b32encode(secrets.token_bytes(length)).decode('utf-8')
    
    @staticmethod
    def get_totp(secret: str, time_step: int = 30) -> str:
        """Generate TOTP code dari secret"""
        secret_bytes = base64.b32decode(secret)
        timestamp = int(time.time() // time_step)
        
        msg = timestamp.to_bytes(8, byteorder='big')
        hmac_result = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
        
        offset = hmac_result[-1] & 0x0f
        code = hmac_result[offset:offset + 4]
        code = int.from_bytes(code, byteorder='big') & 0x7fffffff
        code = code % 1000000
        
        return str(code).zfill(6)
    
    @staticmethod
    def verify_totp(secret: str, code: str, window: int = 1) -> bool:
        """Verify TOTP code dengan toleransi window"""
        try:
            code = str(code).zfill(6)
            
            # Check current dan window sebelumnya/sesudahnya
            for i in range(-window, window + 1):
                timestamp = int((time.time() + (i * 30)) // 30)
                secret_bytes = base64.b32decode(secret)
                
                msg = timestamp.to_bytes(8, byteorder='big')
                hmac_result = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
                
                offset = hmac_result[-1] & 0x0f
                code_bytes = hmac_result[offset:offset + 4]
                code_int = int.from_bytes(code_bytes, byteorder='big') & 0x7fffffff
                code_int = code_int % 1000000
                
                if str(code_int).zfill(6) == code:
                    return True
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_qr_uri(secret: str, email: str, issuer: str = "LoginTabSystem") -> str:
        """Generate QR code URI untuk Google Authenticator"""
        return f"otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}"

class EmailOTP:
    """Email-based One-Time Password"""
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate random OTP"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    @staticmethod
    def generate_otp_with_expiry(db, user_id: int, expiry_minutes: int = 10) -> Tuple[str, str]:
        """Generate OTP dan simpan ke database"""
        otp = EmailOTP.generate_otp()
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        expires_at = (datetime.now() + timedelta(minutes=expiry_minutes)).isoformat()
        
        # Simpan ke tabel otp_tokens
        db.execute(
            '''INSERT INTO otp_tokens (user_id, otp_hash, expires_at) 
               VALUES (?, ?, ?)''',
            (user_id, otp_hash, expires_at)
        )
        
        return otp, expires_at
    
    @staticmethod
    def verify_otp(db, user_id: int, otp: str) -> Tuple[bool, str]:
        """Verify OTP"""
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        
        token = db.fetch_one(
            '''SELECT id, expires_at FROM otp_tokens 
               WHERE user_id = ? AND otp_hash = ? AND used = 0''',
            (user_id, otp_hash)
        )
        
        if not token:
            return False, "OTP tidak ditemukan atau sudah digunakan"
        
        # Check expiry
        expires_at = datetime.fromisoformat(token['expires_at'])
        if datetime.now() > expires_at:
            return False, "OTP sudah expired"
        
        # Mark as used
        db.execute('UPDATE otp_tokens SET used = 1 WHERE id = ?', (token['id'],))
        
        return True, "OTP valid"

class BackupCodes:
    """Backup codes untuk 2FA recovery"""
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list:
        """Generate backup codes"""
        codes = []
        for _ in range(count):
            code = '-'.join([
                secrets.token_hex(2).upper(),
                secrets.token_hex(2).upper(),
                secrets.token_hex(2).upper()
            ])
            codes.append(code)
        return codes
    
    @staticmethod
    def hash_backup_code(code: str) -> str:
        """Hash backup code"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    def verify_backup_code(db, user_id: int, code: str) -> Tuple[bool, str]:
        """Verify dan gunakan backup code"""
        code_hash = BackupCodes.hash_backup_code(code)
        
        backup = db.fetch_one(
            '''SELECT id FROM backup_codes 
               WHERE user_id = ? AND code_hash = ? AND used = 0''',
            (user_id, code_hash)
        )
        
        if not backup:
            return False, "Backup code tidak valid atau sudah digunakan"
        
        # Mark as used
        db.execute('UPDATE backup_codes SET used = 1, used_at = ? WHERE id = ?',
                  (datetime.now().isoformat(), backup['id']))
        
        return True, "Backup code valid"
    
    @staticmethod
    def store_backup_codes(db, user_id: int, codes: list):
        """Store hashed backup codes"""
        for i, code in enumerate(codes, 1):
            code_hash = BackupCodes.hash_backup_code(code)
            db.execute(
                '''INSERT INTO backup_codes (user_id, code_hash, code_index) 
                   VALUES (?, ?, ?)''',
                (user_id, code_hash, i)
            )

class DeviceTrust:
    """Trust device untuk skip 2FA di device tertentu"""
    
    @staticmethod
    def generate_device_token() -> str:
        """Generate unique device token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def trust_device(db, user_id: int, device_name: str, device_token: str, 
                    ip_address: str, user_agent: str, expiry_days: int = 30) -> bool:
        """Tandai device sebagai trusted"""
        expires_at = (datetime.now() + timedelta(days=expiry_days)).isoformat()
        
        db.execute(
            '''INSERT INTO trusted_devices 
               (user_id, device_token, device_name, ip_address, user_agent, expires_at) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, device_token, device_name, ip_address, user_agent, expires_at)
        )
        
        return True
    
    @staticmethod
    def verify_trusted_device(db, user_id: int, device_token: str) -> Tuple[bool, str]:
        """Check apakah device sudah trusted"""
        device = db.fetch_one(
            '''SELECT id, expires_at, device_name FROM trusted_devices 
               WHERE user_id = ? AND device_token = ? AND is_active = 1''',
            (user_id, device_token)
        )
        
        if not device:
            return False, "Device not trusted"
        
        # Check expiry
        expires_at = datetime.fromisoformat(device['expires_at'])
        if datetime.now() > expires_at:
            db.execute('UPDATE trusted_devices SET is_active = 0 WHERE id = ?', (device['id'],))
            return False, "Device trust expired"
        
        return True, device['device_name']
    
    @staticmethod
    def list_trusted_devices(db, user_id: int) -> list:
        """List semua trusted device user"""
        return db.fetch_all(
            '''SELECT id, device_name, ip_address, created_at, expires_at, is_active 
               FROM trusted_devices WHERE user_id = ? ORDER BY created_at DESC''',
            (user_id,)
        )
    
    @staticmethod
    def revoke_device(db, device_id: int):
        """Revoke device trust"""
        db.execute('UPDATE trusted_devices SET is_active = 0 WHERE id = ?', (device_id,))

class SecurityQuestions:
    """Security questions untuk recovery"""
    
    PRESET_QUESTIONS = [
        "Siapa nama hewan peliharaan pertama Anda?",
        "Kota mana tempat Anda lahir?",
        "Apa nama guru favorit Anda di sekolah?",
        "Siapa nama teman dekat Anda di masa kecil?",
        "Apa hobi favorit Anda?",
        "Merek mobil apa yang Anda impikan?",
        "Apa nama jalan tempat Anda tinggal saat ini?",
        "Apa nama sekolah menengah pertama Anda?"
    ]
    
    @staticmethod
    def hash_answer(answer: str) -> str:
        """Hash security question answer"""
        return hashlib.sha256(answer.lower().strip().encode()).hexdigest()
    
    @staticmethod
    def store_security_answers(db, user_id: int, qa_pairs: dict):
        """Store security questions dan answers"""
        for question, answer in qa_pairs.items():
            answer_hash = SecurityQuestions.hash_answer(answer)
            db.execute(
                '''INSERT INTO security_questions (user_id, question, answer_hash) 
                   VALUES (?, ?, ?)''',
                (user_id, question, answer_hash)
            )
    
    @staticmethod
    def verify_security_answer(db, user_id: int, question: str, answer: str) -> bool:
        """Verify security question answer"""
        answer_hash = SecurityQuestions.hash_answer(answer)
        
        result = db.fetch_one(
            '''SELECT id FROM security_questions 
               WHERE user_id = ? AND question = ? AND answer_hash = ?''',
            (user_id, question, answer_hash)
        )
        
        return result is not None
    
    @staticmethod
    def get_user_questions(db, user_id: int, count: int = 2) -> list:
        """Get random security questions untuk user"""
        import random
        
        user_questions = db.fetch_all(
            '''SELECT question FROM security_questions WHERE user_id = ?''',
            (user_id,)
        )
        
        if len(user_questions) >= count:
            return random.sample([q['question'] for q in user_questions], count)
        
        return [q['question'] for q in user_questions]
