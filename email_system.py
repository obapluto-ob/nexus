from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText

from database import get_db, engine, Base
from models import User, EmailBatch, VerifiedEmail
from schemas import UserCreate, EmailVerifyRequest, CampaignSendRequest
from email_verifier import EmailVerifier
from email_sender import EmailSender

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Professional Email Verification & Sender",
    description="Licensed email verification and campaign system",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
email_verifier = EmailVerifier()
email_sender = EmailSender()

@app.post("/register")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user and send license key via email"""
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Generate license key
    license_key = secrets.token_hex(16)
    
    # Create user
    user = User(
        email=user_data.email,
        license_key=license_key,
        is_active=False,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)  # 30-day trial
    )
    
    db.add(user)
    db.commit()
    
    # Send license key via email
    try:
        send_license_email(user_data.email, license_key)
        return {"message": "Registration successful! License key sent to your email."}
    except Exception as e:
        return {"message": "User created but email sending failed", "license_key": license_key}

@app.post("/activate")
async def activate_license(license_key: str, db: Session = Depends(get_db)):
    """Activate user license"""
    
    user = db.query(User).filter(User.license_key == license_key).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid license key")
    
    if user.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="License expired")
    
    user.is_active = True
    db.commit()
    
    return {
        "message": "License activated successfully!",
        "user_email": user.email,
        "expires_at": user.expires_at
    }

@app.post("/verify-emails")
async def verify_emails(
    request: EmailVerifyRequest,
    license_key: str,
    db: Session = Depends(get_db)
):
    """Verify list of emails"""
    
    # Check license
    user = verify_license(license_key, db)
    
    # Create batch
    batch = EmailBatch(
        user_id=user.id,
        total_emails=len(request.emails),
        status="processing"
    )
    db.add(batch)
    db.commit()
    
    # Verify emails
    verified_emails = []
    for email in request.emails:
        try:
            result = await email_verifier.verify_email(email)
            
            verified_email = VerifiedEmail(
                batch_id=batch.id,
                email_address=email,
                is_valid=result['is_valid'],
                verification_status=result['status']
            )
            db.add(verified_email)
            
            if result['is_valid']:
                verified_emails.append({
                    "email": email,
                    "status": result['status'],
                    "valid": True
                })
        except:
            continue
    
    batch.verified_count = len(verified_emails)
    batch.status = "completed"
    db.commit()
    
    return {
        "batch_id": batch.id,
        "total_emails": len(request.emails),
        "verified_emails": len(verified_emails),
        "valid_emails": verified_emails
    }

@app.post("/send-campaign")
async def send_campaign(
    request: CampaignSendRequest,
    license_key: str,
    db: Session = Depends(get_db)
):
    """Send email campaign to verified emails"""
    
    # Check license
    user = verify_license(license_key, db)
    
    # Get verified emails from batch
    verified_emails = db.query(VerifiedEmail).filter(
        VerifiedEmail.batch_id == request.batch_id,
        VerifiedEmail.is_valid == True
    ).all()
    
    if not verified_emails:
        raise HTTPException(status_code=404, detail="No verified emails found")
    
    # Use user's SMTP or default
    smtp_config = {
        'server': request.smtp_server or 'smtp.gmail.com',
        'port': request.smtp_port or 587,
        'username': request.smtp_username or user.email,
        'password': request.smtp_password or 'default_password'
    }
    
    # Send emails
    sent_count = 0
    for email_record in verified_emails:
        try:
            success = send_single_email(
                email_record.email_address,
                request.subject,
                request.content,
                smtp_config
            )
            if success:
                sent_count += 1
        except:
            continue
    
    return {
        "message": "Campaign sent successfully",
        "total_recipients": len(verified_emails),
        "sent_count": sent_count,
        "success_rate": f"{(sent_count/len(verified_emails)*100):.1f}%"
    }

@app.get("/user-stats")
async def get_user_stats(license_key: str, db: Session = Depends(get_db)):
    """Get user statistics"""
    
    user = verify_license(license_key, db)
    
    batches = db.query(EmailBatch).filter(EmailBatch.user_id == user.id).all()
    total_verified = sum(batch.verified_count for batch in batches)
    
    return {
        "user_email": user.email,
        "license_status": "Active" if user.is_active else "Inactive",
        "expires_at": user.expires_at,
        "total_batches": len(batches),
        "total_verified_emails": total_verified
    }

def verify_license(license_key: str, db: Session) -> User:
    """Verify user license"""
    user = db.query(User).filter(User.license_key == license_key).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid license key")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="License not activated")
    
    if user.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="License expired")
    
    return user

def send_license_email(email: str, license_key: str):
    """Send license key to user email"""
    try:
        msg = MIMEText(f"""
        Welcome to Professional Email Verification System!
        
        Your License Key: {license_key}
        
        To activate your account:
        1. Go to the activation page
        2. Enter your license key
        3. Start verifying emails!
        
        Your license is valid for 30 days.
        
        Best regards,
        Email Verification Team
        """)
        
        msg['Subject'] = 'Your Email Verification License Key'
        msg['From'] = 'obedemoni@gmail.com'
        msg['To'] = email
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('obedemoni@gmail.com', 'bfhq ueyu romw anxd')
        server.send_message(msg)
        server.quit()
        
    except Exception as e:
        print(f"Email sending failed: {e}")

def send_single_email(to_email: str, subject: str, content: str, smtp_config: dict) -> bool:
    """Send single email using provided SMTP"""
    try:
        msg = MIMEText(content)
        msg['Subject'] = subject
        msg['From'] = smtp_config['username']
        msg['To'] = to_email
        
        server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
        server.starttls()
        server.login(smtp_config['username'], smtp_config['password'])
        server.send_message(msg)
        server.quit()
        
        return True
    except:
        return False

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)