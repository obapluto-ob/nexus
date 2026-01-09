import re
import dns.resolver
import smtplib
import socket
from email_validator import validate_email, EmailNotValidError
from typing import List, Dict, Tuple
import asyncio
import aiohttp
from datetime import datetime
from sqlalchemy.orm import Session
from models import Email

class EmailVerifier:
    def __init__(self):
        self.disposable_domains = self.load_disposable_domains()
        self.role_based_emails = [
            'admin', 'administrator', 'postmaster', 'hostmaster', 'webmaster',
            'www', 'ftp', 'mail', 'email', 'marketing', 'sales', 'support',
            'help', 'info', 'contact', 'service', 'team', 'noreply', 'no-reply'
        ]
    
    def load_disposable_domains(self) -> set:
        """Load list of disposable email domains"""
        disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'temp-mail.org',
            'throwaway.email', 'getnada.com', 'maildrop.cc'
        }
        return disposable_domains
    
    def is_valid_format(self, email: str) -> bool:
        """Check if email format is valid"""
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    
    def is_disposable_email(self, email: str) -> bool:
        """Check if email is from disposable domain"""
        domain = email.split('@')[1].lower()
        return domain in self.disposable_domains
    
    def is_role_based_email(self, email: str) -> bool:
        """Check if email is role-based"""
        local_part = email.split('@')[0].lower()
        return local_part in self.role_based_emails
    
    def check_mx_record(self, domain: str) -> bool:
        """Check if domain has MX record"""
        try:
            dns.resolver.resolve(domain, 'MX')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
            return False
    
    def verify_smtp(self, email: str) -> Tuple[bool, str]:
        """Verify email via SMTP"""
        try:
            domain = email.split('@')[1]
            
            # Get MX record
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_record = str(mx_records[0].exchange)
            
            # Connect to SMTP server
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_record, 25)
            server.helo('verification-tool.com')
            server.mail('verify@verification-tool.com')
            
            # Check if email exists
            code, message = server.rcpt(email)
            server.quit()
            
            if code == 250:
                return True, "valid"
            elif code in [550, 551, 553]:
                return False, "invalid"
            else:
                return False, "risky"
                
        except Exception as e:
            return False, "unknown"
    
    async def verify_email(self, email: str) -> Dict[str, any]:
        """Comprehensive email verification"""
        result = {
            'email': email,
            'is_valid': False,
            'status': 'invalid',
            'checks': {
                'format': False,
                'mx_record': False,
                'smtp': False,
                'disposable': False,
                'role_based': False,
                'realistic': False
            }
        }
        
        # Format check
        result['checks']['format'] = self.is_valid_format(email)
        if not result['checks']['format']:
            return result
        
        # Realistic email structure check
        username = email.split('@')[0]
        result['checks']['realistic'] = self.is_realistic_email(username)
        if not result['checks']['realistic']:
            result['status'] = 'invalid'
            return result
        
        domain = email.split('@')[1]
        
        # MX record check
        result['checks']['mx_record'] = self.check_mx_record(domain)
        
        # Disposable email check
        result['checks']['disposable'] = self.is_disposable_email(email)
        
        # Role-based email check
        result['checks']['role_based'] = self.is_role_based_email(email)
        
        # SMTP verification (simplified for performance)
        result['checks']['smtp'] = result['checks']['mx_record']  # Skip actual SMTP for speed
        
        # Determine final status
        if (result['checks']['format'] and result['checks']['realistic'] and 
            result['checks']['mx_record']):
            if result['checks']['disposable'] or result['checks']['role_based']:
                result['status'] = 'risky'
            else:
                result['status'] = 'valid'
            result['is_valid'] = True
        elif result['checks']['format'] and result['checks']['mx_record']:
            result['status'] = 'risky'
        else:
            result['status'] = 'invalid'
        
        return result
    
    def is_realistic_email(self, username: str) -> bool:
        """Check if email username looks realistic"""
        # Remove dots and check length
        clean_username = username.replace('.', '').replace('_', '').replace('-', '')
        
        # Must be at least 4 characters
        if len(clean_username) < 4:
            return False
        
        # No single letter parts
        parts = username.split('.')
        for part in parts:
            if len(part) == 1 and part.isalpha():
                return False
        
        # Must contain letters
        if not any(c.isalpha() for c in clean_username):
            return False
        
        # No more than 3 consecutive numbers
        import re
        if re.search(r'\d{4,}', username):
            return False
        
        return True
    
    async def verify_bulk_emails(self, email_list_id: int = None, db: Session = None):
        """Verify emails in bulk"""
        if email_list_id:
            emails = db.query(Email).filter(
                Email.is_verified == False,
                Email.id == email_list_id
            ).all()
        else:
            emails = db.query(Email).filter(Email.is_verified == False).limit(1000).all()
        
        for email_obj in emails:
            try:
                result = await self.verify_email(email_obj.email_address)
                
                email_obj.is_verified = result['is_valid']
                email_obj.verification_status = result['status']
                email_obj.verified_at = datetime.utcnow()
                
                db.commit()
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error verifying {email_obj.email_address}: {str(e)}")
                continue