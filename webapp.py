from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import uvicorn
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
import PyPDF2
import io
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database import get_db, engine
from new_models import User, EmailBatch, VerifiedEmail, Base
from new_schemas import UserCreate, CampaignSendRequest
from email_verifier import EmailVerifier
import hashlib
import platform

# Create tables only if they don't exist
try:
    # Check if database file exists
    import os
    db_exists = os.path.exists('email_tool.db')
    
    Base.metadata.create_all(bind=engine)
    
    if not db_exists:
        print("Database tables created successfully!")
    else:
        print("Database loaded successfully!")
except Exception as e:
    print(f"Database error: {e}")

app = FastAPI(
    title="Professional Email Verification Web App",
    description="Upload files, verify emails, send campaigns",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (create directory if it doesn't exist)
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
email_verifier = EmailVerifier()

@app.post("/register")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user and send license key via email"""
    
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Generate short license key (6 characters: letters + numbers)
    license_key = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(6))
    
    # Create device fingerprint to prevent sharing
    device_info = f"{platform.system()}-{platform.node()}-{user_data.email}"
    device_hash = hashlib.md5(device_info.encode()).hexdigest()[:8]
    
    user = User(
        email=user_data.email,
        license_key=license_key,
        device_hash=device_hash,
        is_active=False,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)  # Auto-renew every 30 days
    )
    
    db.add(user)
    db.commit()
    
    try:
        send_license_email(user_data.email, license_key)
        return {"message": "Registration successful! License key sent to your email."}
    except Exception as e:
        return {"message": "User created but email sending failed", "license_key": license_key}

@app.post("/activate")
async def activate_license(license_key: str, db: Session = Depends(get_db)):
    """Activate user license with device binding"""
    
    user = db.query(User).filter(User.license_key == license_key).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid license key")
    
    # Check if license expired
    if user.expires_at < datetime.utcnow():
        # Auto-renew for 30 more days
        user.expires_at = datetime.utcnow() + timedelta(days=30)
    
    # Create device fingerprint
    device_info = f"{platform.system()}-{platform.node()}-{user.email}"
    current_device_hash = hashlib.md5(device_info.encode()).hexdigest()[:8]
    
    # Check if key is being used on different device
    if user.is_active and user.device_hash != current_device_hash:
        raise HTTPException(status_code=403, detail="License key already activated on another device")
    
    user.is_active = True
    user.device_hash = current_device_hash
    db.commit()
    
    return {
        "message": "License activated successfully!",
        "user_email": user.email,
        "expires_at": user.expires_at,
        "device_bound": True
    }

def send_license_email(email: str, license_key: str):
    """Send license key to user email"""
    try:
        msg = MIMEText(f"""
        NEXUS EMAIL VERIFICATION SYSTEM
        
        Your License Key: {license_key}
        
        To activate your account:
        1. Go to https://nexus-0ajq.onrender.com
        2. Click "ACTIVATE" tab
        3. Enter your license key
        4. Start processing emails
        
        License valid for 30 days with auto-renewal.
        
        System Administrator
        Nexus Email Verification
        """)
        
        msg['Subject'] = 'NEXUS: License Key Generated'
        msg['From'] = os.getenv('SMTP_USERNAME')
        msg['To'] = email
        
        server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
        server.starttls()
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
    except Exception as e:
        print(f"Email sending failed: {e}")

# Keep-alive endpoint
@app.get("/ping")
async def ping():
    return {"status": "alive", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8002))
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Error starting server: {e}")
        input("Press Enter to exit...")