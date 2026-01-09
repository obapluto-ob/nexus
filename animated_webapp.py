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

# Create static directory if it doesn't exist
if not os.path.exists("static"):
    os.makedirs("static")

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
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

# Initialize services
email_verifier = EmailVerifier()

@app.get("/", response_class=HTMLResponse)
async def get_webapp():
    """Serve the animated web application"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Verification System</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #f5576c);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            position: relative;
        }
        
        .floating-shapes {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        }
        
        .shape {
            position: absolute;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
            animation: float 6s ease-in-out infinite;
        }
        
        .shape:nth-child(1) { width: 80px; height: 80px; top: 10%; left: 10%; animation-delay: 0s; }
        .shape:nth-child(2) { width: 60px; height: 60px; top: 20%; right: 10%; animation-delay: 2s; }
        .shape:nth-child(3) { width: 100px; height: 100px; bottom: 10%; left: 20%; animation-delay: 4s; }
        .shape:nth-child(4) { width: 40px; height: 40px; top: 60%; right: 20%; animation-delay: 1s; }
        .shape:nth-child(5) { width: 120px; height: 120px; top: 40%; left: 50%; animation-delay: 3s; }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(180deg); }
        }
        
        .header { 
            background: rgba(255,255,255,0.1); 
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.2);
            color: white; 
            padding: 40px; 
            text-align: center; 
            margin-bottom: 40px; 
            border-radius: 25px;
            position: relative;
            z-index: 10;
            animation: slideDown 1s ease-out;
        }
        
        @keyframes slideDown {
            from { transform: translateY(-100px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .header h1 {
            font-size: 3em;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            animation: glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { text-shadow: 2px 2px 4px rgba(0,0,0,0.3), 0 0 20px rgba(255,255,255,0.5); }
            to { text-shadow: 2px 2px 4px rgba(0,0,0,0.3), 0 0 30px rgba(255,255,255,0.8); }
        }
        
        .card { 
            background: rgba(255,255,255,0.95); 
            backdrop-filter: blur(20px);
            padding: 30px; 
            margin-bottom: 25px; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.3);
            position: relative;
            z-index: 10;
            animation: slideUp 0.8s ease-out;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-10px);
            box-shadow: 0 30px 60px rgba(0,0,0,0.2);
        }
        
        @keyframes slideUp {
            from { transform: translateY(50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .btn { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 15px 30px; 
            border: none; 
            border-radius: 50px; 
            cursor: pointer; 
            margin: 8px; 
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.5s;
        }
        
        .btn:hover::before {
            left: 100%;
        }
        
        .btn:hover { 
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
        }
        
        .btn-success { 
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        }
        
        .btn-success:hover {
            box-shadow: 0 15px 30px rgba(72, 187, 120, 0.4);
        }
        
        .form-group { 
            margin-bottom: 25px;
            animation: fadeInUp 0.6s ease-out;
        }
        
        @keyframes fadeInUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .form-group label { 
            display: block; 
            margin-bottom: 10px; 
            font-weight: 600; 
            color: #2d3748;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .form-group input, .form-group textarea { 
            width: 100%; 
            padding: 15px 20px; 
            border: 2px solid #e2e8f0; 
            border-radius: 15px; 
            font-size: 16px; 
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.9);
        }
        
        .form-group input:focus, .form-group textarea:focus { 
            border-color: #667eea; 
            outline: none;
            transform: scale(1.02);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.2);
        }
        
        .upload-area { 
            border: 3px dashed #cbd5e0; 
            border-radius: 20px; 
            padding: 60px; 
            text-align: center; 
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .upload-area:hover { 
            border-color: #667eea; 
            background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
            transform: scale(1.02);
        }
        
        .upload-area.dragover { 
            border-color: #667eea; 
            background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
            animation: pulse 1s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 25px;
        }
        
        .stat-card { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 25px; 
            border-radius: 20px; 
            text-align: center;
            position: relative;
            overflow: hidden;
            animation: bounceIn 0.8s ease-out;
        }
        
        @keyframes bounceIn {
            0% { transform: scale(0.3); opacity: 0; }
            50% { transform: scale(1.05); }
            70% { transform: scale(0.9); }
            100% { transform: scale(1); opacity: 1; }
        }
        
        .stat-number { 
            font-size: 2.5em; 
            font-weight: 700;
            position: relative;
            z-index: 2;
        }
        
        .tabs { 
            display: flex; 
            margin-bottom: 25px; 
            background: rgba(247, 250, 252, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 15px; 
            padding: 8px;
            border: 1px solid rgba(255,255,255,0.3);
        }
        
        .tab { 
            padding: 15px 25px; 
            border-radius: 10px; 
            cursor: pointer; 
            transition: all 0.3s ease;
            font-weight: 500;
            position: relative;
            overflow: hidden;
        }
        
        .tab.active { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: scale(1.05);
        }
        
        .tab-content { 
            display: none;
            animation: fadeIn 0.5s ease-in;
        }
        
        .tab-content.active { 
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .success { 
            color: #38a169; 
            font-weight: bold; 
            padding: 15px; 
            background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
            border-radius: 15px; 
            margin: 15px 0;
            border-left: 5px solid #38a169;
            animation: slideInRight 0.5s ease-out;
        }
        
        .error { 
            color: #e53e3e; 
            font-weight: bold; 
            padding: 15px; 
            background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
            border-radius: 15px; 
            margin: 15px 0;
            border-left: 5px solid #e53e3e;
            animation: shake 0.5s ease-in-out;
        }
        
        @keyframes slideInRight {
            from { transform: translateX(100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
            20%, 40%, 60%, 80% { transform: translateX(10px); }
        }
        
        .hidden { display: none; }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(102, 126, 234, 0.3);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="floating-shapes">
        <div class="shape"></div>
        <div class="shape"></div>
        <div class="shape"></div>
        <div class="shape"></div>
        <div class="shape"></div>
    </div>

    <div class="header">
        <h1>🚀 Email Verification System</h1>
        <p>Upload • Verify • Send • Succeed</p>
    </div>

    <div class="container">
        <!-- Registration & Activation -->
        <div class="card" id="authSection">
            <div class="tabs">
                <div class="tab active" onclick="showAuthTab('register')">Register</div>
                <div class="tab" onclick="showAuthTab('activate')">Activate</div>
            </div>
            
            <div id="register" class="tab-content active">
                <h2>Get Your License Key</h2>
                <form id="registerForm">
                    <div class="form-group">
                        <label>Your Email Address:</label>
                        <input type="email" id="registerEmail" placeholder="your@email.com" required>
                    </div>
                    <button type="submit" class="btn btn-success">Get License Key</button>
                </form>
                <div id="registerResult"></div>
            </div>

            <div id="activate" class="tab-content">
                <h2>Activate Your License</h2>
                <form id="activateForm">
                    <div class="form-group">
                        <label>License Key:</label>
                        <input type="text" id="licenseKey" placeholder="Enter your license key" required>
                    </div>
                    <button type="submit" class="btn btn-success">Activate License</button>
                </form>
                <div id="activateResult"></div>
            </div>
        </div>

        <!-- Main System -->
        <div class="hidden" id="mainSystem">
            <!-- User Dashboard -->
            <div class="card">
                <h2>📊 Your Dashboard</h2>
                <div id="userStats" class="stats-grid"></div>
            </div>

            <!-- File Upload -->
            <div class="card">
                <h2>📁 Upload & Verify Emails</h2>
                
                <div class="upload-area" id="uploadArea">
                    <h3>📎 Drop files here or click to upload</h3>
                    <p>Supports: CSV, Excel, PDF, TXT files</p>
                    <input type="file" id="fileInput" accept=".csv,.xlsx,.xls,.pdf,.txt" multiple style="display: none;">
                    <button type="button" class="btn" onclick="document.getElementById('fileInput').click()">Choose Files</button>
                </div>
                
                <div id="verificationResults"></div>
            </div>

            <!-- Campaign Sending -->
            <div class="card">
                <h2>📧 Send Email Campaign</h2>
                <form id="campaignForm">
                    <div class="form-group">
                        <label>Batch ID:</label>
                        <input type="number" id="batchId" placeholder="Auto-filled after verification" required>
                    </div>
                    <div class="form-group">
                        <label>Subject:</label>
                        <input type="text" id="campaignSubject" placeholder="Your subject line" required>
                    </div>
                    <div class="form-group">
                        <label>Content:</label>
                        <textarea id="campaignContent" rows="8" placeholder="Your message..." required></textarea>
                    </div>
                    
                    <h3>🔧 SMTP Settings (Optional)</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div class="form-group">
                            <label>SMTP Server:</label>
                            <input type="text" id="smtpServer" placeholder="smtp.gmail.com">
                        </div>
                        <div class="form-group">
                            <label>SMTP Port:</label>
                            <input type="number" id="smtpPort" placeholder="587">
                        </div>
                        <div class="form-group">
                            <label>Username:</label>
                            <input type="email" id="smtpUsername" placeholder="your-email@gmail.com">
                        </div>
                        <div class="form-group">
                            <label>Password:</label>
                            <input type="password" id="smtpPassword" placeholder="your-password">
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-success">🚀 Send Campaign</button>
                </form>
                <div id="campaignResults"></div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8002';
        let currentLicenseKey = '';

        // Auth tab switching
        function showAuthTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tab).classList.add('active');
        }

        // File upload handling
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            handleFiles(files);
        });

        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });

        async function handleFiles(files) {
            if (!currentLicenseKey) {
                alert('Please activate your license first!');
                return;
            }

            for (let file of files) {
                await uploadAndVerifyFile(file);
            }
            
            loadUserStats();
        }

        async function uploadAndVerifyFile(file) {
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch(`${API_BASE}/upload-verify?license_key=${currentLicenseKey}`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    displayVerificationResults(result, file.name);
                    document.getElementById('batchId').value = result.batch_id;
                } else {
                    showError('verificationResults', `Error processing ${file.name}: ${result.detail}`);
                }
            } catch (error) {
                showError('verificationResults', `Error uploading ${file.name}: ${error.message}`);
            }
        }

        function displayVerificationResults(result, filename) {
            const resultsDiv = document.getElementById('verificationResults');
            
            const resultHTML = `
                <div class="card" style="margin-top: 20px;">
                    <h3>📊 Results for: ${filename}</h3>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">${result.batch_id}</div>
                            <div>Batch ID</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${result.total_emails}</div>
                            <div>Total Emails</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${result.valid_count}</div>
                            <div>Valid Emails</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${((result.valid_count/result.total_emails)*100).toFixed(1)}%</div>
                            <div>Success Rate</div>
                        </div>
                    </div>
                </div>
            `;
            
            resultsDiv.innerHTML = resultHTML;
        }

        // Registration
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
                    showSuccess('registerResult', result.message);
                } else {
                    showError('registerResult', result.detail);
                }
                
            } catch (error) {
                showError('registerResult', `Error: ${error.message}`);
            }
        });

        // Activation
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
                    showSuccess('activateResult', result.message);
                    
                    // Show main system
                    document.getElementById('authSection').classList.add('hidden');
                    document.getElementById('mainSystem').classList.remove('hidden');
                    loadUserStats();
                } else {
                    showError('activateResult', result.detail);
                }
                
            } catch (error) {
                showError('activateResult', `Error: ${error.message}`);
            }
        });

        // Campaign sending
        document.getElementById('campaignForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const campaignData = {
                batch_id: parseInt(document.getElementById('batchId').value),
                subject: document.getElementById('campaignSubject').value,
                content: document.getElementById('campaignContent').value,
                smtp_server: document.getElementById('smtpServer').value || null,
                smtp_port: parseInt(document.getElementById('smtpPort').value) || null,
                smtp_username: document.getElementById('smtpUsername').value || null,
                smtp_password: document.getElementById('smtpPassword').value || null
            };
            
            try {
                const response = await fetch(`${API_BASE}/send-campaign?license_key=${currentLicenseKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(campaignData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    document.getElementById('campaignResults').innerHTML = `
                        <div class="success">
                            <h4>🎉 Campaign Sent Successfully!</h4>
                            <p><strong>Total Recipients:</strong> ${result.total_recipients}</p>
                            <p><strong>Sent Successfully:</strong> ${result.sent_count}</p>
                            <p><strong>Success Rate:</strong> ${result.success_rate}</p>
                        </div>
                    `;
                } else {
                    showError('campaignResults', result.detail);
                }
                
            } catch (error) {
                showError('campaignResults', `Error: ${error.message}`);
            }
        });

        async function loadUserStats() {
            try {
                const response = await fetch(`${API_BASE}/user-stats?license_key=${currentLicenseKey}`);
                const stats = await response.json();
                
                document.getElementById('userStats').innerHTML = `
                    <div class="stat-card">
                        <div class="stat-number">👤</div>
                        <div>${stats.user_email}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.license_status}</div>
                        <div>License Status</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_batches}</div>
                        <div>Total Batches</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_verified_emails}</div>
                        <div>Verified Emails</div>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        function showSuccess(elementId, message) {
            document.getElementById(elementId).innerHTML = `<div class="success">${message}</div>`;
        }

        function showError(elementId, message) {
            document.getElementById(elementId).innerHTML = `<div class="error">${message}</div>`;
        }
    </script>
</body>
</html>
    """

@app.post("/register")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user and send license key via email"""
    
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    license_key = secrets.token_hex(16)
    
    user = User(
        email=user_data.email,
        license_key=license_key,
        is_active=False,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30)
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

@app.post("/upload-verify")
async def upload_and_verify_file(
    file: UploadFile = File(...),
    license_key: str = "",
    db: Session = Depends(get_db)
):
    """Upload file and verify emails"""
    
    user = verify_license(license_key, db)
    
    # Extract emails from file
    emails = await extract_emails_from_file(file)
    
    if not emails:
        raise HTTPException(status_code=400, detail="No emails found in file")
    
    # Create batch
    batch = EmailBatch(
        user_id=user.id,
        total_emails=len(emails),
        status="processing"
    )
    db.add(batch)
    db.commit()
    
    # Verify emails
    valid_emails = []
    invalid_emails = []
    risky_emails = []
    
    for email in emails:
        try:
            result = await email_verifier.verify_email(email)
            
            verified_email = VerifiedEmail(
                batch_id=batch.id,
                email_address=email,
                is_valid=result['is_valid'],
                verification_status=result['status']
            )
            db.add(verified_email)
            
            email_data = {"email": email, "status": result['status']}
            
            if result['status'] == 'valid':
                valid_emails.append(email_data)
            elif result['status'] == 'risky':
                risky_emails.append(email_data)
            else:
                invalid_emails.append(email_data)
                
        except:
            invalid_emails.append({"email": email, "status": "error"})
    
    batch.verified_count = len(valid_emails)
    batch.status = "completed"
    db.commit()
    
    # Combine all emails for display
    categorized_emails = valid_emails + risky_emails + invalid_emails
    
    return {
        "batch_id": batch.id,
        "total_emails": len(emails),
        "valid_count": len(valid_emails),
        "risky_count": len(risky_emails),
        "invalid_count": len(invalid_emails),
        "categorized_emails": categorized_emails
    }

@app.post("/send-campaign")
async def send_campaign(
    request: CampaignSendRequest,
    license_key: str,
    db: Session = Depends(get_db)
):
    """Send email campaign to verified emails"""
    
    user = verify_license(license_key, db)
    
    verified_emails = db.query(VerifiedEmail).filter(
        VerifiedEmail.batch_id == request.batch_id,
        VerifiedEmail.is_valid == True
    ).all()
    
    if not verified_emails:
        raise HTTPException(status_code=404, detail="No verified emails found")
    
    smtp_config = {
        'server': request.smtp_server or 'smtp.gmail.com',
        'port': request.smtp_port or 587,
        'username': request.smtp_username or 'obedemoni@gmail.com',
        'password': request.smtp_password or 'bfhq ueyu romw anxd'
    }
    
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

async def extract_emails_from_file(file: UploadFile) -> List[str]:
    """Extract emails from uploaded file"""
    emails = []
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    try:
        content = await file.read()
        
        if file.filename.endswith('.pdf'):
            # Extract from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            emails = email_pattern.findall(text)
            
        elif file.filename.endswith(('.csv', '.xlsx', '.xls')):
            # Extract from CSV/Excel
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(content))
            else:
                df = pd.read_excel(io.BytesIO(content))
            
            # Look for email columns
            for col in df.columns:
                if 'email' in col.lower() or df[col].astype(str).str.contains('@').any():
                    column_emails = df[col].dropna().astype(str).tolist()
                    for email in column_emails:
                        if email_pattern.match(email):
                            emails.append(email)
                            
        else:
            # Extract from text file
            text = content.decode('utf-8', errors='ignore')
            emails = email_pattern.findall(text)
    
    except Exception as e:
        print(f"Error extracting emails: {e}")
    
    # Remove duplicates
    return list(set(emails))

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
        🚀 Welcome to Professional Email Verification System!
        
        Your License Key: {license_key}
        
        To activate your account:
        1. Go to http://localhost:8002
        2. Click "Activate" tab
        3. Enter your license key
        4. Start verifying emails!
        
        Your license is valid for 30 days.
        
        Best regards,
        Email Verification Team
        """)
        
        msg['Subject'] = '🔑 Your Email Verification License Key'
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