from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import uvicorn
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
import pandas as pd
import PyPDF2
import io
import re
import os

from database import get_db, engine
from new_models import User, EmailBatch, VerifiedEmail, Base
from new_schemas import UserCreate, CampaignSendRequest
from email_verifier import EmailVerifier
import hashlib
import platform

# Create tables only if they don't exist
try:
    db_exists = os.path.exists('email_tool.db')
    Base.metadata.create_all(bind=engine)
    if not db_exists:
        print("Database tables created successfully!")
    else:
        print("Database loaded successfully!")
except Exception as e:
    print(f"Database error: {e}")

app = FastAPI(title="NEXUS Email Verification System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

email_verifier = EmailVerifier()

@app.get("/", response_class=HTMLResponse)
async def get_webapp():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS Email Verification</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0a0a0a; color: #fff; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: rgba(255,255,255,0.05); padding: 40px; text-align: center; margin-bottom: 30px; border-radius: 20px; }
        .header h1 { font-size: 3rem; background: linear-gradient(135deg, #00ffff, #0080ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .card { background: rgba(255,255,255,0.05); padding: 30px; margin-bottom: 25px; border-radius: 20px; }
        .tabs { display: flex; margin-bottom: 25px; background: rgba(255,255,255,0.05); border-radius: 12px; padding: 8px; }
        .tab { padding: 12px 25px; border-radius: 8px; cursor: pointer; transition: all 0.3s; }
        .tab.active { background: linear-gradient(135deg, #00ffff, #0080ff); color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .btn { background: linear-gradient(135deg, #00ff88, #00cc66); color: white; padding: 15px 30px; border: none; border-radius: 12px; cursor: pointer; margin: 8px; }
        .form-group { margin-bottom: 25px; }
        .form-group label { display: block; margin-bottom: 10px; font-weight: 600; }
        .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 15px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 12px; color: #fff; }
        .hidden { display: none; }
        .success { color: #00ff88; padding: 15px; background: rgba(0,255,136,0.1); border-radius: 12px; margin: 15px 0; }
        .error { color: #ff4757; padding: 15px; background: rgba(255,71,87,0.1); border-radius: 12px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>NEXUS EMAIL VERIFICATION</h1>
        <p>Advanced Email Intelligence • Real-time Verification • Campaign Automation</p>
    </div>

    <div class="container">
        <div class="card" id="authSection">
            <div class="tabs">
                <div class="tab active" onclick="showAuthTab('register')">REGISTER</div>
                <div class="tab" onclick="showAuthTab('activate')">ACTIVATE</div>
            </div>
            
            <div id="register" class="tab-content active">
                <h2>Generate License Key</h2>
                <form id="registerForm">
                    <div class="form-group">
                        <label>Email Address:</label>
                        <input type="email" id="registerEmail" required>
                    </div>
                    <button type="submit" class="btn">Generate License Key</button>
                </form>
                <div id="registerResult"></div>
            </div>

            <div id="activate" class="tab-content">
                <h2>Activate License</h2>
                <form id="activateForm">
                    <div class="form-group">
                        <label>License Key:</label>
                        <input type="text" id="licenseKey" required>
                    </div>
                    <button type="submit" class="btn">Activate System</button>
                </form>
                <div id="activateResult"></div>
            </div>
        </div>

        <div class="hidden" id="mainSystem">
            <div class="card">
                <h2>System Dashboard</h2>
                <div id="userStats"></div>
            </div>

            <div class="card">
                <h2>Email Processing Engine</h2>
                <div class="tabs">
                    <div class="tab active" onclick="showProcessTab('paste')">Paste Emails</div>
                    <div class="tab" onclick="showProcessTab('generate')">Lead Hunter</div>
                </div>
                
                <div id="paste" class="tab-content active">
                    <div class="form-group">
                        <label>Paste Your Emails Here:</label>
                        <textarea id="emailTextArea" rows="10" placeholder="Paste emails here..."></textarea>
                    </div>
                    <button type="button" class="btn" onclick="processTextEmails()">Process Emails</button>
                </div>
                
                <div id="generate" class="tab-content">
                    <h3>Lead Hunter Engine</h3>
                    <div class="form-group">
                        <label>Email Count:</label>
                        <input type="number" id="emailCount" value="1000" min="100" max="10000">
                    </div>
                    <button type="button" class="btn" onclick="generateEmails()">Hunt & Verify Leads</button>
                </div>
                
                <div id="verificationResults"></div>
            </div>

            <div class="card">
                <h2>Campaign Deployment</h2>
                <form id="campaignForm">
                    <div class="form-group">
                        <label>Batch ID:</label>
                        <input type="number" id="batchId" required>
                    </div>
                    <div class="form-group">
                        <label>Subject Line:</label>
                        <input type="text" id="campaignSubject" required>
                    </div>
                    <div class="form-group">
                        <label>Message Content:</label>
                        <textarea id="campaignContent" rows="8" required></textarea>
                    </div>
                    <button type="submit" class="btn">Deploy Campaign</button>
                </form>
                <div id="campaignResults"></div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8002';
        let currentLicenseKey = '';

        function showAuthTab(tab) {
            document.querySelectorAll('#authSection .tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('#authSection .tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tab).classList.add('active');
        }

        function showProcessTab(tab) {
            document.querySelectorAll('.card .tabs .tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.card .tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tab).classList.add('active');
        }

        async function processTextEmails() {
            if (!currentLicenseKey) {
                alert('Please activate your license first!');
                return;
            }
            const emailText = document.getElementById('emailTextArea').value;
            if (!emailText.trim()) {
                alert('Please paste some emails first!');
                return;
            }
            // Process emails logic here
            alert('Processing emails...');
        }

        async function generateEmails() {
            if (!currentLicenseKey) {
                alert('Please activate your license first!');
                return;
            }
            // Generate emails logic here
            alert('Generating emails...');
        }

        document.getElementById('registerForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('registerEmail').value;
            try {
                const response = await fetch(`${API_BASE}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email })
                });
                const result = await response.json();
                if (response.ok) {
                    document.getElementById('registerResult').innerHTML = `<div class="success">${result.message}</div>`;
                } else {
                    document.getElementById('registerResult').innerHTML = `<div class="error">${result.detail}</div>`;
                }
            } catch (error) {
                document.getElementById('registerResult').innerHTML = `<div class="error">Error: ${error.message}</div>`;
            }
        });

        document.getElementById('activateForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const licenseKey = document.getElementById('licenseKey').value;
            try {
                const response = await fetch(`${API_BASE}/activate?license_key=${licenseKey}`, {
                    method: 'POST'
                });
                const result = await response.json();
                if (response.ok) {
                    currentLicenseKey = licenseKey;
                    document.getElementById('activateResult').innerHTML = `<div class="success">${result.message}</div>`;
                    document.getElementById('authSection').classList.add('hidden');
                    document.getElementById('mainSystem').classList.remove('hidden');
                } else {
                    document.getElementById('activateResult').innerHTML = `<div class="error">${result.detail}</div>`;
                }
            } catch (error) {
                document.getElementById('activateResult').innerHTML = `<div class="error">Error: ${error.message}</div>`;
            }
        });
    </script>
</body>
</html>
    """

# Add all your existing endpoints here...
@app.post("/register")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    license_key = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(6))
    device_info = f"{platform.system()}-{platform.node()}-{user_data.email}"
    device_hash = hashlib.md5(device_info.encode()).hexdigest()[:8]
    
    user = User(
        email=user_data.email,
        license_key=license_key,
        device_hash=device_hash,
        is_active=False,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    db.add(user)
    db.commit()
    
    return {"message": f"Registration successful! Your license key: {license_key}"}

@app.post("/activate")
async def activate_license(license_key: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.license_key == license_key).first()
    if not user:
        raise HTTPException(status_code=404, detail="Invalid license key")
    
    user.is_active = True
    db.commit()
    
    return {"message": "License activated successfully!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)