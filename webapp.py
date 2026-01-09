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

@app.get("/", response_class=HTMLResponse)
async def get_webapp():
    """Serve the main web application"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Verification System</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #0e1a2e 100%);
            color: #ffffff;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: radial-gradient(circle at 20% 80%, rgba(0,255,255,0.1) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(0,128,255,0.1) 0%, transparent 50%),
                        radial-gradient(circle at 40% 40%, rgba(128,0,255,0.05) 0%, transparent 50%);
            animation: float 20s ease-in-out infinite;
        }
        
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        }
        
        .particle {
            position: absolute;
            width: 2px;
            height: 2px;
            background: rgba(0,255,255,0.6);
            border-radius: 50%;
            animation: float-particle 15s infinite linear;
        }
        
        @keyframes float-particle {
            0% { transform: translateY(100vh) translateX(0); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-10vh) translateX(100px); opacity: 0; }
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        .header { 
            background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
            backdrop-filter: blur(30px); 
            border: 1px solid rgba(255,255,255,0.2);
            color: white; 
            padding: 50px; 
            text-align: center; 
            margin-bottom: 40px; 
            border-radius: 28px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 30px 60px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.2);
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: conic-gradient(from 0deg, transparent, rgba(0,255,255,0.1), transparent, rgba(0,128,255,0.1), transparent);
            animation: rotate 15s linear infinite;
        }
        
        .header h1 {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00ffff, #0080ff, #8000ff, #ff0080);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15px;
            position: relative;
            z-index: 1;
            text-shadow: 0 0 30px rgba(0,255,255,0.5);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.8;
            position: relative;
            z-index: 1;
        }
        
        .card { 
            background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
            backdrop-filter: blur(25px);
            border: 1px solid rgba(255,255,255,0.15);
            padding: 35px; 
            margin-bottom: 30px; 
            border-radius: 24px; 
            box-shadow: 0 25px 50px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
            transition: left 0.8s;
        }
        
        .card:hover::before {
            left: 100%;
        }
        
        .card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 35px 70px rgba(0,255,255,0.2), inset 0 1px 0 rgba(255,255,255,0.2);
            border-color: rgba(0,255,255,0.3);
        }
        
        .btn { 
            background: linear-gradient(135deg, #00ffff, #0080ff, #8000ff);
            color: white; 
            padding: 16px 32px; 
            border: none; 
            border-radius: 16px; 
            cursor: pointer; 
            margin: 10px; 
            font-weight: 600; 
            font-size: 14px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,255,255,0.3);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.6s;
        }
        
        .btn:hover::before {
            left: 100%;
        }
        
        .btn:hover { 
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 15px 35px rgba(0,255,255,0.4);
            background: linear-gradient(135deg, #00ffff, #0080ff, #ff00ff);
        }
        
        .btn:active {
            transform: translateY(-1px) scale(1.02);
        }
        
        .btn-success { 
            background: linear-gradient(135deg, #00ff88, #00cc66);
        }
        
        .btn-success:hover { 
            box-shadow: 0 10px 25px rgba(0,255,136,0.3);
        }
        
        .form-group { margin-bottom: 25px; }
        
        .form-group label { 
            display: block; 
            margin-bottom: 10px; 
            font-weight: 600; 
            color: #ffffff;
            font-size: 14px;
        }
        
        .form-group input, .form-group textarea, .form-group select { 
            width: 100%; 
            padding: 15px; 
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2); 
            border-radius: 12px; 
            font-size: 14px; 
            color: #ffffff;
            transition: all 0.3s ease;
        }
        
        .form-group select option {
            background: #2d2d2d;
            color: #ffffff;
        }
        
        .form-group input::placeholder, .form-group textarea::placeholder {
            color: rgba(255,255,255,0.5);
        }
        
        .form-group input:focus, .form-group textarea:focus { 
            border-color: #00ffff; 
            outline: none;
            box-shadow: 0 0 20px rgba(0,255,255,0.2);
        }
        
        .hidden { display: none; }
        
        .success { 
            color: #00ff88; 
            font-weight: bold; 
            padding: 15px; 
            background: rgba(0,255,136,0.1); 
            border: 1px solid rgba(0,255,136,0.3);
            border-radius: 12px; 
            margin: 15px 0; 
        }
        
        .error { 
            color: #ff4757; 
            font-weight: bold; 
            padding: 15px; 
            background: rgba(255,71,87,0.1); 
            border: 1px solid rgba(255,71,87,0.3);
            border-radius: 12px; 
            margin: 15px 0; 
        }
        
        .upload-area { 
            border: 2px dashed rgba(255,255,255,0.3); 
            border-radius: 15px; 
            padding: 50px; 
            text-align: center; 
            background: rgba(255,255,255,0.02); 
            transition: all 0.3s ease;
            position: relative;
        }
        
        .upload-area:hover { 
            border-color: #00ffff; 
            background: rgba(0,255,255,0.05);
            transform: scale(1.02);
        }
        
        .upload-area.dragover { 
            border-color: #00ffff; 
            background: rgba(0,255,255,0.1);
            box-shadow: 0 0 30px rgba(0,255,255,0.3);
        }
        
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 25px; 
        }
        
        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .stat-card { 
            background: linear-gradient(145deg, rgba(0,255,255,0.15), rgba(0,128,255,0.1), rgba(128,0,255,0.05)); 
            border: 1px solid rgba(255,255,255,0.2);
            color: white; 
            padding: 30px; 
            border-radius: 20px; 
            text-align: center;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(20px);
        }
        
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #00ffff, #0080ff, #8000ff);
            transform: scaleX(0);
            transition: transform 0.4s;
        }
        
        .stat-card:hover::before {
            transform: scaleX(1);
        }
        
        .stat-card:hover {
            transform: translateY(-8px) scale(1.05);
            box-shadow: 0 20px 40px rgba(0,255,255,0.3);
            background: linear-gradient(145deg, rgba(0,255,255,0.2), rgba(0,128,255,0.15), rgba(128,0,255,0.1));
        }
        
        .stat-number { 
            font-size: 2.5em; 
            font-weight: 700;
            background: linear-gradient(135deg, #00ffff, #0080ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .email-results { 
            max-height: 400px; 
            overflow-y: auto; 
            border: 1px solid rgba(255,255,255,0.1); 
            border-radius: 12px;
            background: rgba(0,0,0,0.2);
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            33% { transform: translateY(-20px) rotate(1deg); }
            66% { transform: translateY(10px) rotate(-1deg); }
        }
        
        .email-item {
            padding: 15px; 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .email-item::before {
            content: '';
            position: absolute;
            left: -100%;
            top: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0,255,255,0.1), transparent);
            transition: left 0.5s;
        }
        
        .email-item:hover::before {
            left: 100%;
        }
        
        .email-item:hover {
            background: rgba(255,255,255,0.08);
            transform: translateX(5px);
        }
        
        .email-valid { background: rgba(0,255,136,0.1); }
        .email-invalid { background: rgba(255,71,87,0.1); }
        .email-risky { background: rgba(255,193,7,0.1); }
        
        .progress-bar { 
            width: 100%; 
            height: 10px; 
            background: rgba(255,255,255,0.1); 
            border-radius: 5px; 
            overflow: hidden; 
            margin: 15px 0; 
        }
        
        .progress-fill { 
            height: 100%; 
            background: linear-gradient(90deg, #00ffff, #00ff88); 
            transition: width 0.3s ease;
        }
        
        .tabs { 
            display: flex; 
            margin-bottom: 30px; 
            background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
            border-radius: 16px; 
            padding: 8px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
        }
        
        .tabs::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(0,255,255,0.5), transparent);
            animation: scan 3s infinite;
        }
        
        @keyframes scan {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .tab { 
            padding: 15px 30px; 
            border-radius: 12px; 
            cursor: pointer; 
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            font-weight: 600;
            position: relative;
            overflow: hidden;
        }
        
        .tab::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transition: left 0.5s;
        }
        
        .tab:hover::before {
            left: 100%;
        }
        
        .tab.active { 
            background: linear-gradient(135deg, #00ffff, #0080ff, #8000ff); 
            color: white;
            box-shadow: 0 8px 25px rgba(0,255,255,0.4);
            transform: translateY(-2px);
        }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .tech-icon {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 8px;
            background: linear-gradient(135deg, #00ffff, #0080ff);
            border-radius: 3px;
        }
        
        .terminal-container {
            background: #1a1a1a;
            border: 1px solid rgba(0,255,255,0.3);
            border-radius: 8px;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            box-shadow: 0 0 20px rgba(0,255,255,0.1);
        }
        
        .terminal-header {
            background: #2d2d2d;
            padding: 10px 15px;
            border-bottom: 1px solid rgba(0,255,255,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 8px 8px 0 0;
        }
        
        .terminal-title {
            color: #00ffff;
            font-size: 12px;
            font-weight: bold;
        }
        
        .terminal-controls {
            display: flex;
            gap: 6px;
        }
        
        .control-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        
        .control-dot.red { background: #ff5f56; }
        .control-dot.yellow { background: #ffbd2e; }
        .control-dot.green { background: #27ca3f; }
        
        .terminal-body {
            padding: 15px;
            height: 200px;
            overflow-y: auto;
            background: #0a0a0a;
            color: #00ff00;
            font-size: 13px;
            line-height: 1.4;
        }
        
        .terminal-line {
            margin-bottom: 2px;
            animation: typewriter 0.5s ease-in;
        }
        
        .terminal-line.loading {
            color: #ffa502;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }
        
        .terminal-line.success { color: #00ff88; }
        .terminal-line.error { color: #ff4757; }
        .terminal-line.warning { color: #ffa502; }
        .terminal-line.info { color: #00ffff; }
        
        @keyframes typewriter {
            from { opacity: 0; transform: translateX(-10px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .cursor {
            display: inline-block;
            background: #00ff00;
            width: 8px;
            height: 14px;
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        .content-options {
            margin-bottom: 10px;
        }
        
        .content-options select {
            width: 200px;
            padding: 8px;
            background: #2d2d2d;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            color: #ffffff;
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header { padding: 20px; }
            .header h1 { font-size: 2rem; }
            .stats-grid { grid-template-columns: 1fr; }
            .card { padding: 20px; }
            .btn { padding: 12px 20px; margin: 5px; }
            .tabs { flex-direction: column; }
            .tab { margin-bottom: 5px; }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <div class="particles" id="particles"></div>
    
    <div class="header">
        <h1>NEXUS EMAIL VERIFICATION</h1>
        <p>Advanced Email Intelligence • Real-time Verification • Campaign Automation</p>
    </div>

    <div class="container">
        <!-- Registration & Activation -->
        <div class="card" id="authSection">
            <div class="tabs">
                <div class="tab active" onclick="showAuthTab('register')">
                    <span class="tech-icon"></span>REGISTER
                </div>
                <div class="tab" onclick="showAuthTab('activate')">
                    <span class="tech-icon"></span>ACTIVATE
                </div>
            </div>
            
            <div id="register" class="tab-content active">
                <h2>Generate License Key</h2>
                <form id="registerForm">
                    <div class="form-group">
                        <label>Email Address:</label>
                        <input type="email" id="registerEmail" placeholder="your@email.com" required>
                    </div>
                    <button type="submit" class="btn btn-success">Generate License Key</button>
                </form>
                <div id="registerResult"></div>
            </div>

            <div id="activate" class="tab-content">
                <h2>Activate License</h2>
                <form id="activateForm">
                    <div class="form-group">
                        <label>License Key:</label>
                        <input type="text" id="licenseKey" placeholder="Enter 6-character license key" required>
                    </div>
                    <button type="submit" class="btn btn-success">Activate System</button>
                </form>
                <div id="activateResult"></div>
            </div>
        </div>

        <!-- Main System -->
        <div class="hidden" id="mainSystem">
            <!-- User Dashboard -->
            <div class="card">
                <h2>System Dashboard</h2>
                <div id="userStats" class="stats-grid"></div>
            </div>

            <!-- Batch Manager -->
            <div class="card">
                <h2>Batch Manager</h2>
                <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
                    <button type="button" class="btn" onclick="loadAllBatches()">Refresh Batches</button>
                    <input type="text" id="searchBatches" placeholder="Search leads..." style="flex: 1; min-width: 200px; padding: 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white;" oninput="searchLeads()">
                    <select id="filterStatus" onchange="filterLeads()" style="padding: 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white;">
                        <option value="all">All Status</option>
                        <option value="valid">Valid Only</option>
                        <option value="risky">Risky Only</option>
                        <option value="invalid">Invalid Only</option>
                    </select>
                </div>
                <div id="batchList"></div>
            </div>

            <!-- File Upload & Email Verification -->
            <div class="card">
                <h2>Email Processing Engine</h2>
                
                <div class="tabs">
                    <div class="tab active" onclick="showProcessTab('upload')">File Upload</div>
                    <div class="tab" onclick="showProcessTab('paste')">Paste Emails</div>
                    <div class="tab" onclick="showProcessTab('generate')">Lead Hunter</div>
                </div>
                
                <div id="upload" class="tab-content active">
                    <div class="upload-area" id="uploadArea">
                        <h3>File Upload Interface</h3>
                        <p>Supported formats: CSV, Excel, PDF, TXT</p>
                        <input type="file" id="fileInput" accept=".csv,.xlsx,.xls,.pdf,.txt" multiple style="display: none;">
                        <button type="button" class="btn" onclick="document.getElementById('fileInput').click()">Select Files</button>
                    </div>
                </div>
                
                <div id="paste" class="tab-content">
                    <div class="form-group">
                        <label>Paste Your Emails Here:</label>
                        <textarea id="emailTextArea" rows="10" placeholder="Paste emails here (one per line or separated by commas, spaces, etc.)\n\nexample@email.com\nuser@domain.com\ntest@company.org" style="font-family: monospace;"></textarea>
                    </div>
                    <button type="button" class="btn btn-success" onclick="processTextEmails()">Process Emails</button>
                </div>
                
                <div id="generate" class="tab-content">
                    <h3>Lead Hunter Engine</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div class="form-group">
                            <label>Email Count:</label>
                            <input type="number" id="emailCount" value="1000" min="100" max="10000">
                        </div>
                        <div class="form-group">
                            <label>Target Industry:</label>
                            <select id="industry">
                                <option value="trading">Trading/Investment</option>
                                <option value="banking">Banking/Finance</option>
                                <option value="insurance">Insurance</option>
                                <option value="fintech">FinTech/Crypto</option>
                                <option value="wealth">Wealth Management</option>
                                <option value="accounting">Accounting/Tax</option>
                                <option value="real_estate">Real Estate</option>
                                <option value="mixed">Mixed Financial</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Geographic Region:</label>
                            <select id="region">
                                <option value="us">United States</option>
                                <option value="uk">United Kingdom</option>
                                <option value="eu">European Union</option>
                                <option value="asia">Asia Pacific</option>
                                <option value="kenya">Kenya</option>
                                <option value="nigeria">Nigeria</option>
                                <option value="south_africa">South Africa</option>
                                <option value="india">India</option>
                                <option value="china">China</option>
                                <option value="japan">Japan</option>
                                <option value="global">Global Mix</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Job Level:</label>
                            <select id="jobLevel">
                                <option value="executive">C-Level/Executive</option>
                                <option value="senior">Senior Management</option>
                                <option value="manager">Manager Level</option>
                                <option value="analyst">Analyst/Associate</option>
                                <option value="mixed">All Levels</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Email Providers:</label>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                            <label><input type="checkbox" id="gmail" checked> Gmail</label>
                            <label><input type="checkbox" id="yahoo" checked> Yahoo</label>
                            <label><input type="checkbox" id="outlook" checked> Outlook</label>
                            <label><input type="checkbox" id="icloud" checked> iCloud</label>
                            <label><input type="checkbox" id="business" checked> Business Domains</label>
                        </div>
                    </div>
                    <button type="button" class="btn btn-success" onclick="generateEmails()">Hunt & Verify Leads</button>
                </div>
                
                <div id="uploadProgress" class="hidden">
                    <div class="terminal-container">
                        <div class="terminal-header">
                            <span class="terminal-title">NEXUS PROCESSING ENGINE</span>
                            <div class="terminal-controls">
                                <span class="control-dot red"></span>
                                <span class="control-dot yellow"></span>
                                <span class="control-dot green"></span>
                            </div>
                        </div>
                        <div class="terminal-body" id="terminalOutput">
                            <div class="terminal-line">$ nexus-email-processor --init</div>
                        </div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                    </div>
                </div>
                
                <div id="verificationResults"></div>
            </div>

            <!-- Campaign Sending -->
            <div class="card">
                <h2>Campaign Deployment</h2>
                <form id="campaignForm">
                    <div class="form-group">
                        <label>Batch ID:</label>
                        <input type="number" id="batchId" placeholder="Auto-populated after verification" required>
                    </div>
                    <div class="form-group">
                        <label>Subject Line:</label>
                        <input type="text" id="campaignSubject" placeholder="Campaign subject" required>
                    </div>
                    <div class="form-group">
                        <label>Message Content:</label>
                        <div class="content-options">
                            <select id="fontStyle" onchange="updateContentFont()">
                                <option value="default">Default Font</option>
                                <option value="business">Business Professional</option>
                                <option value="modern">Modern Sans</option>
                                <option value="classic">Classic Serif</option>
                                <option value="tech">Tech Monospace</option>
                                <option value="handwritten">Handwritten Style</option>
                            </select>
                        </div>
                        <textarea id="campaignContent" rows="8" placeholder="Campaign message content..." required></textarea>
                    </div>
                    
                    <h3>SMTP Configuration</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div class="form-group">
                            <label>SMTP Server:</label>
                            <input type="text" id="smtpServer" placeholder="smtp.gmail.com">
                        </div>
                        <div class="form-group">
                            <label>Port:</label>
                            <input type="number" id="smtpPort" placeholder="587">
                        </div>
                        <div class="form-group">
                            <label>Username:</label>
                            <input type="email" id="smtpUsername" placeholder="your-email@gmail.com">
                        </div>
                        <div class="form-group">
                            <label>Password:</label>
                            <input type="password" id="smtpPassword" placeholder="app-password">
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-success">Deploy Campaign</button>
                </form>
                <div id="campaignResults"></div>
                
                <div id="campaignProgress" class="hidden">
                    <div class="terminal-container">
                        <div class="terminal-header">
                            <span class="terminal-title">CAMPAIGN DEPLOYMENT ENGINE</span>
                            <div class="terminal-controls">
                                <span class="control-dot red"></span>
                                <span class="control-dot yellow"></span>
                                <span class="control-dot green"></span>
                            </div>
                        </div>
                        <div class="terminal-body" id="campaignTerminal">
                            <div class="terminal-line">$ nexus-campaign-deployer --init</div>
                        </div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="campaignProgressFill" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Create floating particles
        function createParticles() {
            const container = document.getElementById('particles');
            for (let i = 0; i < 50; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 15 + 's';
                particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
                container.appendChild(particle);
            }
        }
        
        // Initialize particles on load
        window.addEventListener('load', createParticles);

        const API_BASE = 'http://localhost:8002';
        let currentLicenseKey = '';
        function showAuthTab(tab) {
            document.querySelectorAll('#authSection .tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('#authSection .tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tab).classList.add('active');
        }

        // Process tab switching
        function showProcessTab(tab) {
            document.querySelectorAll('.card .tabs .tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.card .tab-content').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tab).classList.add('active');
        }

        // Add terminal line for campaign deployment
        function addCampaignTerminalLine(text, type = '') {
            const terminal = document.getElementById('campaignTerminal');
            const line = document.createElement('div');
            line.className = `terminal-line ${type}`;
            line.textContent = `> ${text}`;
            terminal.appendChild(line);
            terminal.scrollTop = terminal.scrollHeight;
        }
        
        // Generate AI emails
        async function generateEmails() {
            if (!currentLicenseKey) {
                alert('Please activate your license first!');
                return;
            }

            const count = document.getElementById('emailCount').value;
            const industry = document.getElementById('industry').value;
            const region = document.getElementById('region').value;
            const jobLevel = document.getElementById('jobLevel').value;
            const providers = {
                gmail: document.getElementById('gmail').checked,
                yahoo: document.getElementById('yahoo').checked,
                outlook: document.getElementById('outlook').checked,
                icloud: document.getElementById('icloud').checked,
                business: document.getElementById('business').checked
            };

            document.getElementById('uploadProgress').classList.remove('hidden');
            initTerminal();
            
            addTerminalLine('Initializing Lead Hunter engine...', 'info');
            
            const huntingInterval = showLoadingDots('terminalOutput', `Hunting ${count} leads for ${industry} industry`);
            
            try {
                const response = await fetch(`${API_BASE}/generate-emails?license_key=${currentLicenseKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ count: parseInt(count), industry, region, jobLevel, providers })
                });

                stopLoadingDots(huntingInterval);
                const result = await response.json();

                if (response.ok) {
                    addTerminalLine(`Hunted ${result.total_emails} lead addresses`, 'success');
                    
                    const verifyInterval = showLoadingDots('terminalOutput', 'Verifying lead quality');
                    await new Promise(resolve => setTimeout(resolve, 3000));
                    stopLoadingDots(verifyInterval);
                    
                    document.getElementById('progressFill').style.width = '100%';
                    
                    addTerminalLine(`Verification complete: ${result.valid_count} valid, ${result.invalid_count} invalid`, 'success');
                    addTerminalLine(`Success rate: ${((result.valid_count/result.total_emails)*100).toFixed(1)}%`, 'success');
                    
                    displayVerificationResults(result, 'Lead Hunter Results');
                    document.getElementById('batchId').value = result.batch_id;
                } else {
                    addTerminalLine(`Error: ${result.detail}`, 'error');
                }
            } catch (error) {
                stopLoadingDots(huntingInterval);
                addTerminalLine(`Network error: ${error.message}`, 'error');
            }
            
            addTerminalLine('Lead hunting completed successfully', 'success');
            setTimeout(() => {
                document.getElementById('uploadProgress').classList.add('hidden');
            }, 1000);
            loadUserStats();
        }
        
        // Update content font style
        function updateContentFont() {
            const fontStyle = document.getElementById('fontStyle').value;
            const textarea = document.getElementById('campaignContent');
            
            switch(fontStyle) {
                case 'business':
                    textarea.style.fontFamily = 'Times New Roman, serif';
                    break;
                case 'modern':
                    textarea.style.fontFamily = 'Arial, Helvetica, sans-serif';
                    break;
                case 'classic':
                    textarea.style.fontFamily = 'Georgia, serif';
                    break;
                case 'tech':
                    textarea.style.fontFamily = 'Courier New, monospace';
                    break;
                case 'handwritten':
                    textarea.style.fontFamily = 'Brush Script MT, cursive';
                    break;
                default:
                    textarea.style.fontFamily = 'Inter, sans-serif';
            }
        }
            const fontStyle = document.getElementById('fontStyle').value;
            const textarea = document.getElementById('campaignContent');
            
            switch(fontStyle) {
                case 'business':
                    textarea.style.fontFamily = 'Times New Roman, serif';
                    break;
                case 'modern':
                    textarea.style.fontFamily = 'Arial, Helvetica, sans-serif';
                    break;
                case 'classic':
                    textarea.style.fontFamily = 'Georgia, serif';
                    break;
                case 'tech':
                    textarea.style.fontFamily = 'Courier New, monospace';
                    break;
                case 'handwritten':
                    textarea.style.fontFamily = 'Brush Script MT, cursive';
                    break;
                default:
                    textarea.style.fontFamily = 'Inter, sans-serif';
        }
        
        // Process pasted emails
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

            document.getElementById('uploadProgress').classList.remove('hidden');
            initTerminal();
            
            const parseInterval = showLoadingDots('terminalOutput', 'Processing pasted email text');
            
            try {
                const response = await fetch(`${API_BASE}/process-text?license_key=${currentLicenseKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: emailText })
                });

                stopLoadingDots(parseInterval);
                const result = await response.json();

                if (response.ok) {
                    addTerminalLine(`Found ${result.total_emails} email addresses`, 'success');
                    
                    const verifyInterval = showLoadingDots('terminalOutput', 'Verifying email addresses');
                    await new Promise(resolve => setTimeout(resolve, 2500));
                    stopLoadingDots(verifyInterval);
                    
                    document.getElementById('progressFill').style.width = '100%';
                    
                    addTerminalLine(`Verification complete: ${result.valid_count} valid, ${result.invalid_count} invalid`, 'success');
                    addTerminalLine(`Success rate: ${((result.valid_count/result.total_emails)*100).toFixed(1)}%`, 'success');
                    
                    displayVerificationResults(result, 'Pasted Emails');
                    document.getElementById('batchId').value = result.batch_id;
                } else {
                    addTerminalLine(`Error: ${result.detail}`, 'error');
                }
            } catch (error) {
                stopLoadingDots(parseInterval);
                addTerminalLine(`Network error: ${error.message}`, 'error');
            }
            
            addTerminalLine('Process completed successfully', 'success');
            setTimeout(() => {
                document.getElementById('uploadProgress').classList.add('hidden');
            }, 1000);
            loadUserStats();
        }
        
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

            document.getElementById('uploadProgress').classList.remove('hidden');
            initTerminal();
            
            for (let i = 0; i < files.length; i++) {
                await uploadAndVerifyFile(files[i], i + 1, files.length);
            }
            
            addTerminalLine('Process completed successfully', 'success');
            setTimeout(() => {
                document.getElementById('uploadProgress').classList.add('hidden');
            }, 1000);
            loadUserStats();
        }

        function initTerminal() {
            const terminal = document.getElementById('terminalOutput');
            terminal.innerHTML = '<div class="terminal-line">$ nexus-email-processor --init</div>';
            addTerminalLine('Initializing email verification engine...', 'info');
            addTerminalLine('Loading AI models and validation rules...', 'info');
            addTerminalLine('System ready for processing', 'success');
        }

        function addTerminalLine(text, type = '') {
            const terminal = document.getElementById('terminalOutput');
            const line = document.createElement('div');
            line.className = `terminal-line ${type}`;
            line.textContent = `> ${text}`;
            terminal.appendChild(line);
            terminal.scrollTop = terminal.scrollHeight;
        }
        
        function showLoadingDots(elementId, message) {
            const terminal = document.getElementById(elementId);
            let dots = 0;
            const loadingLine = document.createElement('div');
            loadingLine.className = 'terminal-line loading';
            loadingLine.id = 'loading-line';
            terminal.appendChild(loadingLine);
            
            const interval = setInterval(() => {
                dots = (dots + 1) % 4;
                loadingLine.textContent = `> ${message}${'.'.repeat(dots)}`;
            }, 500);
            
            return interval;
        }
        
        function stopLoadingDots(intervalId) {
            clearInterval(intervalId);
            const loadingLine = document.getElementById('loading-line');
            if (loadingLine) loadingLine.remove();
        }

        async function uploadAndVerifyFile(file, fileIndex, totalFiles) {
            const formData = new FormData();
            formData.append('file', file);

            addTerminalLine(`Processing file ${fileIndex}/${totalFiles}: ${file.name}`, 'info');
            
            const loadingInterval = showLoadingDots('terminalOutput', 'Extracting email addresses');
            
            try {
                const response = await fetch(`${API_BASE}/upload-verify?license_key=${currentLicenseKey}`, {
                    method: 'POST',
                    body: formData
                });

                stopLoadingDots(loadingInterval);
                const result = await response.json();

                if (response.ok) {
                    addTerminalLine(`Found ${result.total_emails} email addresses`, 'success');
                    
                    const verifyInterval = showLoadingDots('terminalOutput', 'Verifying emails');
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    stopLoadingDots(verifyInterval);
                    
                    document.getElementById('progressFill').style.width = '100%';
                    
                    addTerminalLine(`Verification complete: ${result.valid_count} valid, ${result.invalid_count} invalid`, 'success');
                    addTerminalLine(`Success rate: ${((result.valid_count/result.total_emails)*100).toFixed(1)}%`, 'success');
                    
                    displayVerificationResults(result, file.name);
                    document.getElementById('batchId').value = result.batch_id;
                } else {
                    addTerminalLine(`Error: ${result.detail}`, 'error');
                }
            } catch (error) {
                stopLoadingDots(loadingInterval);
                addTerminalLine(`Network error: ${error.message}`, 'error');
            }
        }

        function displayVerificationResults(result, filename) {
            const resultsDiv = document.getElementById('verificationResults');
            
            const resultHTML = `
                <div class="card" style="margin-top: 20px;">
                    <h3>Analysis Results: ${filename}</h3>
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
                    
                    <h4>Email Status Breakdown:</h4>
                    <div class="email-results">
                        ${result.categorized_emails.map(email => `
                            <div class="email-item email-${email.status}">
                                <span>${email.email}</span>
                                <span><strong>${email.status.toUpperCase()}</strong></span>
                            </div>
                        `).join('')}
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
            
            const deployBtn = e.target.querySelector('button[type="submit"]');
            deployBtn.disabled = true;
            deployBtn.textContent = 'Deploying...';
            
            // Show campaign terminal first
            document.getElementById('campaignProgress').classList.remove('hidden');
            addCampaignTerminalLine('Initializing campaign deployment...', 'info');
            
            const campaignData = {
                batch_id: parseInt(document.getElementById('batchId').value),
                subject: document.getElementById('campaignSubject').value,
                content: document.getElementById('campaignContent').value,
                smtp_server: document.getElementById('smtpServer').value || null,
                smtp_port: parseInt(document.getElementById('smtpPort').value) || null,
                smtp_username: document.getElementById('smtpUsername').value || null,
                smtp_password: document.getElementById('smtpPassword').value || null
            };
            
            addCampaignTerminalLine(`Loading batch ${campaignData.batch_id} recipients...`, 'info');
            
            // Add delay to show terminal first
            await new Promise(resolve => setTimeout(resolve, 500));
            
            try {
                const response = await fetch(`${API_BASE}/send-campaign?license_key=${currentLicenseKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(campaignData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    addCampaignTerminalLine(`Found ${result.total_recipients} verified recipients`, 'success');
                    addCampaignTerminalLine('Starting email deployment...', 'info');
                    
                    // Show sending progress with delays
                    for (let i = 1; i <= result.total_recipients; i++) {
                        const progress = (i / result.total_recipients * 100).toFixed(0);
                        document.getElementById('campaignProgressFill').style.width = `${progress}%`;
                        addCampaignTerminalLine(`Sending email ${i}/${result.total_recipients} (${progress}%)`, '');
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }
                    
                    addCampaignTerminalLine(`Campaign deployed: ${result.sent_count}/${result.total_recipients} sent`, 'success');
                    addCampaignTerminalLine(`Success rate: ${result.success_rate}`, 'success');
                    
                    document.getElementById('campaignResults').innerHTML = `
                        <div class="success">
                            <h4>Campaign Deployed Successfully</h4>
                            <p><strong>Total Recipients:</strong> ${result.total_recipients}</p>
                            <p><strong>Sent Successfully:</strong> ${result.sent_count}</p>
                            <p><strong>Success Rate:</strong> ${result.success_rate}</p>
                        </div>
                    `;
                } else {
                    addCampaignTerminalLine(`Error: ${result.detail}`, 'error');
                    showError('campaignResults', result.detail);
                }
                
            } catch (error) {
                addCampaignTerminalLine(`Network error: ${error.message}`, 'error');
                showError('campaignResults', `Error: ${error.message}`);
            }
            
            addCampaignTerminalLine('Deployment completed', 'success');
            // Keep terminal visible - don't hide it
            deployBtn.disabled = false;
            deployBtn.textContent = 'Deploy Campaign';
        });

        async function loadAllBatches() {
            const btn = event?.target;
            if (btn) {
                btn.disabled = true;
                btn.textContent = 'Loading...';
            }
            
            try {
                const response = await fetch(`${API_BASE}/batches?license_key=${currentLicenseKey}`);
                const batches = await response.json();
                
                const batchHTML = batches.map(batch => `
                    <div class="card" style="margin: 10px 0; padding: 20px;">
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-number">${batch.id}</div>
                                <div>Batch ID</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${batch.total_emails}</div>
                                <div>Total Emails</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${batch.valid_count}</div>
                                <div>Valid</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${batch.risky_count}</div>
                                <div>Risky</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${batch.invalid_count}</div>
                                <div>Invalid</div>
                            </div>
                        </div>
                        <div style="margin-top: 15px;">
                            <button class="btn" onclick="viewBatch(${batch.id}, event)">View Details</button>
                            <button class="btn btn-success" onclick="downloadBatch(${batch.id}, 'pdf', event)">Download PDF</button>
                            <button class="btn" onclick="deleteBatch(${batch.id}, event)" style="background: #ff4757;">Delete Batch</button>
                        </div>
                    </div>
                `).join('');
                
                document.getElementById('batchList').innerHTML = batchHTML || '<p>No batches found</p>';
            } catch (error) {
                console.error('Error loading batches:', error);
            }
            
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Refresh Batches';
            }
        }
        
        async function viewBatch(batchId, event) {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Loading...';
            
            try {
                const response = await fetch(`${API_BASE}/batch/${batchId}?license_key=${currentLicenseKey}`);
                const batch = await response.json();
                
                const emailsHTML = batch.emails.map(email => `
                    <div class="email-item email-${email.status}">
                        <span>${email.email}</span>
                        <span><strong>${email.status.toUpperCase()}</strong></span>
                    </div>
                `).join('');
                
                document.getElementById('verificationResults').innerHTML = `
                    <div class="card">
                        <h3>Batch ${batchId} Details</h3>
                        <div class="email-results">${emailsHTML}</div>
                    </div>
                `;
            } catch (error) {
                console.error('Error viewing batch:', error);
            }
            
            btn.disabled = false;
            btn.textContent = 'View Details';
        }
        
        async function deleteBatch(batchId, event) {
            if (!confirm('Are you sure you want to delete this batch?')) return;
            
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Deleting...';
            
            try {
                const response = await fetch(`${API_BASE}/delete-batch/${batchId}?license_key=${currentLicenseKey}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    loadAllBatches();
                    loadUserStats();
                } else {
                    alert('Error deleting batch');
                    btn.disabled = false;
                    btn.textContent = 'Delete Batch';
                }
            } catch (error) {
                console.error('Error deleting batch:', error);
                btn.disabled = false;
                btn.textContent = 'Delete Batch';
            }
        }
        
        async function downloadBatch(batchId, type, event) {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Generating PDF...';
            
            try {
                const response = await fetch(`${API_BASE}/download-batch/${batchId}?type=${type}&license_key=${currentLicenseKey}`);
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `batch_${batchId}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error('Error downloading batch:', error);
            }
            
            btn.disabled = false;
            btn.textContent = 'Download PDF';
        }

        function showSuccess(elementId, message) {
            document.getElementById(elementId).innerHTML = `<div class="success">${message}</div>`;
        }

        async function loadUserStats() {
            try {
                const response = await fetch(`${API_BASE}/user-stats?license_key=${currentLicenseKey}`);
                const stats = await response.json();
                
                document.getElementById('userStats').innerHTML = `
                    <div class="stat-card">
                        <div class="stat-number">USER</div>
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
                    <div class="stat-card" onclick="viewAllLeads()" style="cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        <div class="stat-number">${stats.total_verified_emails}</div>
                        <div>Verified Emails</div>
                        <div style="font-size: 12px; color: #00ffff; margin-top: 5px;">Click to view all</div>
                    </div>
                `;
                
                loadAllBatches();
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        async function viewAllLeads() {
            try {
                const response = await fetch(`${API_BASE}/all-leads?license_key=${currentLicenseKey}`);
                const leads = await response.json();
                
                const leadsHTML = `
                    <div class="card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <h3>All Verified Leads (${leads.length})</h3>
                            <div>
                                <button class="btn btn-success" onclick="downloadAllLeads('valid')">Download Valid PDF</button>
                                <button class="btn" onclick="downloadAllLeads('all')">Download All PDF</button>
                                <button class="btn" onclick="downloadAllLeads('csv')">Download CSV</button>
                            </div>
                        </div>
                        <div class="email-results" style="max-height: 500px;">
                            ${leads.map(lead => `
                                <div class="email-item email-${lead.status}">
                                    <span>${lead.email}</span>
                                    <span><strong>${lead.status.toUpperCase()}</strong></span>
                                    <span style="font-size: 12px; opacity: 0.7;">Batch ${lead.batch_id}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
                
                document.getElementById('verificationResults').innerHTML = leadsHTML;
            } catch (error) {
                console.error('Error loading all leads:', error);
            }
        }
        
        function searchLeads() {
            const searchTerm = document.getElementById('searchBatches').value.toLowerCase();
            const emailItems = document.querySelectorAll('.email-item');
            
            emailItems.forEach(item => {
                const email = item.textContent.toLowerCase();
                item.style.display = email.includes(searchTerm) ? 'flex' : 'none';
            });
        }
        
        function filterLeads() {
            const filterStatus = document.getElementById('filterStatus').value;
            const emailItems = document.querySelectorAll('.email-item');
            
            emailItems.forEach(item => {
                if (filterStatus === 'all') {
                    item.style.display = 'flex';
                } else {
                    const hasStatus = item.classList.contains(`email-${filterStatus}`);
                    item.style.display = hasStatus ? 'flex' : 'none';
                }
            });
        }
        
        async function downloadAllLeads(type) {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = type === 'csv' ? 'Generating CSV...' : 'Generating PDF...';
            
            try {
                const response = await fetch(`${API_BASE}/download-all-leads?type=${type}&license_key=${currentLicenseKey}`);
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = type === 'csv' ? `all_leads.csv` : `all_leads_${type}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error('Error downloading leads:', error);
            }
            
            btn.disabled = false;
            btn.textContent = btn.textContent.includes('CSV') ? 'Download CSV' : (btn.textContent.includes('Valid') ? 'Download Valid PDF' : 'Download All PDF');
        }
    </script>
</body>
</html>
    """

@app.get("/batches")
async def get_user_batches(license_key: str, db: Session = Depends(get_db)):
    user = verify_license(license_key, db)
    
    batches = db.query(EmailBatch).filter(EmailBatch.user_id == user.id).all()
    
    batch_data = []
    for batch in batches:
        emails = db.query(VerifiedEmail).filter(VerifiedEmail.batch_id == batch.id).all()
        valid_count = len([e for e in emails if e.verification_status == 'valid'])
        risky_count = len([e for e in emails if e.verification_status == 'risky'])
        invalid_count = len([e for e in emails if e.verification_status == 'invalid'])
        
        batch_data.append({
            "id": batch.id,
            "total_emails": batch.total_emails,
            "valid_count": valid_count,
            "risky_count": risky_count,
            "invalid_count": invalid_count,
            "created_at": batch.created_at
        })
    
    return batch_data

@app.get("/batch/{batch_id}")
async def get_batch_details(batch_id: int, license_key: str, db: Session = Depends(get_db)):
    user = verify_license(license_key, db)
    
    batch = db.query(EmailBatch).filter(EmailBatch.id == batch_id, EmailBatch.user_id == user.id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    emails = db.query(VerifiedEmail).filter(VerifiedEmail.batch_id == batch_id).all()
    
    return {
        "batch_id": batch_id,
        "emails": [{"email": e.email_address, "status": e.verification_status} for e in emails]
    }

@app.delete("/delete-batch/{batch_id}")
async def delete_batch(batch_id: int, license_key: str, db: Session = Depends(get_db)):
    user = verify_license(license_key, db)
    
    batch = db.query(EmailBatch).filter(EmailBatch.id == batch_id, EmailBatch.user_id == user.id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    db.query(VerifiedEmail).filter(VerifiedEmail.batch_id == batch_id).delete()
    db.delete(batch)
    db.commit()
    
    return {"message": "Batch deleted successfully"}

@app.get("/all-leads")
async def get_all_leads(license_key: str, db: Session = Depends(get_db)):
    user = verify_license(license_key, db)
    
    emails = db.query(VerifiedEmail).join(EmailBatch).filter(
        EmailBatch.user_id == user.id
    ).all()
    
    return [{"email": e.email_address, "status": e.verification_status, "batch_id": e.batch_id} for e in emails]

@app.get("/download-all-leads")
async def download_all_leads(type: str, license_key: str, db: Session = Depends(get_db)):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from fastapi.responses import StreamingResponse
    import io
    
    user = verify_license(license_key, db)
    
    emails = db.query(VerifiedEmail).join(EmailBatch).filter(
        EmailBatch.user_id == user.id
    )
    
    if type == 'valid':
        emails = emails.filter(VerifiedEmail.verification_status == 'valid')
    
    emails = emails.all()
    
    if type == 'csv':
        output = io.StringIO()
        output.write("email,status,batch_id\n")
        for email in emails:
            output.write(f"{email.email_address},{email.verification_status},{email.batch_id}\n")
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=all_leads.csv"}
        )
    else:
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        p.drawString(100, 750, f"All Leads Report - {type.upper()}")
        p.drawString(100, 730, f"Total Leads: {len(emails)}")
        
        y = 700
        for email in emails:
            if y < 50:
                p.showPage()
                y = 750
            p.drawString(100, y, f"{email.email_address} - {email.verification_status} (Batch {email.batch_id})")
            y -= 20
        
        p.save()
        buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(buffer.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=all_leads_{type}.pdf"}
        )
async def delete_batch(batch_id: int, license_key: str, db: Session = Depends(get_db)):
    user = verify_license(license_key, db)
    
    batch = db.query(EmailBatch).filter(EmailBatch.id == batch_id, EmailBatch.user_id == user.id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    db.query(VerifiedEmail).filter(VerifiedEmail.batch_id == batch_id).delete()
    db.delete(batch)
    db.commit()
    
    return {"message": "Batch deleted successfully"}

@app.get("/download-batch/{batch_id}")
async def download_batch(batch_id: int, type: str, license_key: str, db: Session = Depends(get_db)):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from fastapi.responses import StreamingResponse
    import io
    
    user = verify_license(license_key, db)
    
    batch = db.query(EmailBatch).filter(EmailBatch.id == batch_id, EmailBatch.user_id == user.id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    emails = db.query(VerifiedEmail).filter(VerifiedEmail.batch_id == batch_id).all()
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.drawString(100, 750, f"Email Batch Report - ID: {batch_id}")
    p.drawString(100, 730, f"Total Emails: {len(emails)}")
    
    y = 700
    for email in emails:
        if y < 50:
            p.showPage()
            y = 750
        p.drawString(100, y, f"{email.email_address} - {email.verification_status}")
        y -= 20
    
    p.save()
    buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(buffer.getvalue()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=batch_{batch_id}.pdf"}
    )
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

@app.post("/generate-emails")
async def generate_emails(
    request: dict,
    license_key: str,
    db: Session = Depends(get_db)
):
    """Generate AI emails using names and domains"""
    
    user = verify_license(license_key, db)
    
    count = request.get('count', 1000)
    industry = request.get('industry', 'trading')
    region = request.get('region', 'us')
    job_level = request.get('jobLevel', 'mixed')
    providers = request.get('providers', {})
    
    # Advanced name databases by region
    names_by_region = {
        'us': {
            'first': ['alexander', 'benjamin', 'christopher', 'daniel', 'ethan', 'franklin', 'gabriel', 'harrison', 'isaac', 'jackson', 'katherine', 'lillian', 'margaret', 'natalie', 'olivia', 'penelope', 'quinn', 'rebecca', 'samantha', 'theodore', 'victoria', 'william', 'xavier', 'yvonne', 'zachary'],
            'last': ['anderson', 'brooks', 'campbell', 'davidson', 'edwards', 'fitzgerald', 'goldman', 'harrison', 'jefferson', 'kennedy', 'lawrence', 'mitchell', 'nelson', 'peterson', 'richardson', 'sullivan', 'thompson', 'wellington', 'washington', 'zimmerman']
        },
        'uk': {
            'first': ['alistair', 'benedict', 'charlotte', 'dominic', 'elizabeth', 'frederick', 'georgina', 'henry', 'isabella', 'james', 'katherine', 'lawrence', 'margaret', 'nicholas', 'olivia', 'philippa', 'quentin', 'rosalind', 'sebastian', 'theodora'],
            'last': ['ashworth', 'blackwood', 'churchill', 'davidson', 'ellsworth', 'fairfax', 'gloucester', 'hamilton', 'kensington', 'lancaster', 'montgomery', 'northcott', 'pemberton', 'queensbury', 'rothschild', 'stratford', 'wellington', 'whitmore', 'yorkshire', 'cambridge']
        },
        'eu': {
            'first': ['alessandro', 'bernard', 'christoph', 'dimitri', 'elena', 'francesco', 'guillaume', 'heinrich', 'isabella', 'jacques', 'kristina', 'lorenzo', 'marguerite', 'nicolas', 'ophelia', 'philippe', 'quintus', 'rosalie', 'stefan', 'theodore'],
            'last': ['andersson', 'bernard', 'christensen', 'dubois', 'eriksson', 'ferrari', 'garcia', 'hansen', 'ivanov', 'johansson', 'kowalski', 'larsson', 'mueller', 'nielsen', 'olsson', 'petrov', 'rossi', 'schmidt', 'torres', 'weber']
        },
        'asia': {
            'first': ['akira', 'benjamin', 'chen', 'david', 'emily', 'feng', 'grace', 'hiroshi', 'ivan', 'james', 'kevin', 'lily', 'michael', 'nancy', 'oscar', 'peter', 'qing', 'robert', 'sophia', 'thomas'],
            'last': ['chen', 'kim', 'lee', 'liu', 'ng', 'park', 'singh', 'tan', 'wang', 'wong', 'yamamoto', 'zhang', 'zhao', 'lim', 'ho', 'wu', 'xu', 'yang', 'li', 'huang']
        },
        'kenya': {
            'first': ['abdi', 'amina', 'brian', 'catherine', 'daniel', 'esther', 'francis', 'grace', 'hassan', 'irene', 'james', 'khadija', 'lawrence', 'mary', 'nicholas', 'olivia', 'peter', 'rachel', 'samuel', 'tabitha', 'victor', 'wanjiku', 'xavier', 'yvonne', 'zainab'],
            'last': ['kamau', 'wanjiku', 'mwangi', 'njoroge', 'ochieng', 'achieng', 'kiprotich', 'cheruiyot', 'wafula', 'otieno', 'maina', 'karanja', 'gitau', 'mbugua', 'macharia', 'kimani', 'mutua', 'kinyua', 'wairimu', 'gathoni']
        },
        'nigeria': {
            'first': ['adebayo', 'blessing', 'chinedu', 'deborah', 'emeka', 'fatima', 'gabriel', 'hauwa', 'ibrahim', 'joy', 'kemi', 'lawrence', 'mercy', 'ngozi', 'olumide', 'patience', 'queen', 'rasheed', 'solomon', 'tunde', 'uche', 'victoria', 'wisdom', 'yemi', 'zainab'],
            'last': ['adebayo', 'okafor', 'williams', 'johnson', 'ibrahim', 'mohammed', 'aliyu', 'bello', 'ahmed', 'usman', 'abdullahi', 'musa', 'suleiman', 'garba', 'yakubu', 'ismail', 'hassan', 'yusuf', 'abubakar', 'sadiq']
        },
        'south_africa': {
            'first': ['andile', 'bongiwe', 'chuma', 'dineo', 'eugene', 'fatima', 'graham', 'hlengiwe', 'isaac', 'jane', 'kagiso', 'lerato', 'mandla', 'nomsa', 'oscar', 'palesa', 'quinton', 'refilwe', 'sipho', 'thabo', 'unathi', 'vanessa', 'wesley', 'xolani', 'yolanda'],
            'last': ['nkomo', 'mthembu', 'dlamini', 'ndlovu', 'mokoena', 'mabena', 'mahlangu', 'molefe', 'mokwena', 'sithole', 'zwane', 'khumalo', 'maseko', 'ngcobo', 'sibiya', 'mnguni', 'hadebe', 'cele', 'zulu', 'shabalala']
        },
        'india': {
            'first': ['aarav', 'ananya', 'arjun', 'diya', 'ishaan', 'kavya', 'krishna', 'meera', 'nikhil', 'priya', 'rahul', 'shreya', 'varun', 'aditi', 'amit', 'deepika', 'harsh', 'neha', 'rohan', 'sanya', 'vikram', 'pooja', 'karan', 'riya', 'dev'],
            'last': ['sharma', 'gupta', 'singh', 'kumar', 'verma', 'agarwal', 'jain', 'bansal', 'mehta', 'shah', 'patel', 'malhotra', 'chopra', 'sinha', 'joshi', 'saxena', 'pandey', 'mishra', 'tiwari', 'dubey']
        },
        'china': {
            'first': ['wei', 'ming', 'lei', 'yan', 'jun', 'li', 'jing', 'hui', 'bin', 'xin', 'hao', 'yu', 'qiang', 'na', 'gang', 'fang', 'ping', 'tao', 'dan', 'rui', 'chao', 'ling', 'feng', 'xia', 'bo'],
            'last': ['wang', 'li', 'zhang', 'liu', 'chen', 'yang', 'huang', 'zhao', 'wu', 'zhou', 'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'he', 'gao', 'lin', 'luo']
        },
        'japan': {
            'first': ['hiroshi', 'yuki', 'takeshi', 'akiko', 'kenji', 'naomi', 'satoshi', 'miyuki', 'kazuki', 'emi', 'ryota', 'sayuri', 'daiki', 'yui', 'shota', 'mai', 'kenta', 'rina', 'yuya', 'miki', 'ryo', 'nana', 'sota', 'ai', 'haruto'],
            'last': ['tanaka', 'suzuki', 'takahashi', 'watanabe', 'ito', 'yamamoto', 'nakamura', 'kobayashi', 'kato', 'yoshida', 'yamada', 'sasaki', 'yamaguchi', 'matsumoto', 'inoue', 'kimura', 'hayashi', 'shimizu', 'yamazaki', 'mori']
        }
    }
    
    # Job-level prefixes
    job_prefixes = {
        'executive': ['ceo', 'cfo', 'cto', 'president', 'vp', 'director'],
        'senior': ['senior', 'head', 'lead', 'principal', 'manager'],
        'manager': ['manager', 'supervisor', 'coordinator', 'team.lead'],
        'analyst': ['analyst', 'associate', 'specialist', 'advisor']
    }
    
    # Select names based on region
    if region == 'global':
        all_first = []
        all_last = []
        for r in names_by_region.values():
            all_first.extend(r['first'])
            all_last.extend(r['last'])
        first_names = all_first
        last_names = all_last
    else:
        first_names = names_by_region[region]['first']
        last_names = names_by_region[region]['last']
    
    # Domain lists
    business_domains = ['tradingview.com', 'schwab.com', 'fidelity.com', 'etrade.com', 'robinhood.com', 'tdameritrade.com', 'interactivebrokers.com', 'ally.com', 'vanguard.com', 'merrilledge.com', 'wellsfargo.com', 'jpmorgan.com', 'goldmansachs.com', 'morganstanley.com', 'blackrock.com', 'statestreet.com', 'bnpparibas.com', 'deutschebank.com', 'creditsuisse.com', 'ubs.com', 'hsbc.com', 'barclays.com', 'lloyds.com', 'rbs.com', 'santander.com', 'bbva.com', 'unicredit.it', 'bnl.it', 'intesasanpaolo.com', 'commerzbank.de', 'dbs.com', 'ocbc.com', 'uob.com', 'maybank.com', 'cimb.com', 'bca.co.id', 'mandiri.co.id', 'bni.co.id', 'bri.co.id', 'icbc.com.cn']
    
    personal_domains = []
    if providers.get('gmail'): personal_domains.extend(['gmail.com'] * 40)
    if providers.get('yahoo'): personal_domains.extend(['yahoo.com', 'yahoo.co.uk'] * 20)
    if providers.get('outlook'): personal_domains.extend(['outlook.com', 'hotmail.com'] * 15)
    if providers.get('icloud'): personal_domains.extend(['icloud.com', 'me.com'] * 10)
    
    generated_emails = []
    
    for i in range(count):
        first = secrets.choice(first_names)
        last = secrets.choice(last_names)
        
        # Add job-level patterns
        if job_level != 'mixed' and providers.get('business') and secrets.randbelow(100) < 40:
            prefix = secrets.choice(job_prefixes[job_level])
            patterns = [
                f"{prefix}.{first}.{last}",
                f"{prefix}{first[0]}{last}",
                f"{first}.{last}.{prefix}"
            ]
        else:
            # Realistic patterns only
            patterns = [
                f"{first}.{last}",
                f"{first}{last}",
                f"{first[0]}.{last}",
                f"{first}.{last[0]}.{secrets.randbelow(99)+10}"
            ]
        
        username = secrets.choice(patterns)
        
        # Ensure minimum length and no single letters
        if len(username.replace('.', '').replace('@', '')) < 4:
            username = f"{first}.{last}"
        
        # Choose domain based on providers
        if providers.get('business') and secrets.randbelow(100) < 30:
            domain = secrets.choice(business_domains)
        else:
            domain = secrets.choice(personal_domains) if personal_domains else 'gmail.com'
        
        email = f"{username}@{domain}"
        
        # Skip if email looks fake (single letters, too short)
        if len(username.replace('.', '')) >= 4 and not any(part in ['m', 'r', 's', 'k', 'a', 'b', 'c', 'd'] for part in username.split('.')):
            generated_emails.append(email)
    
    # Remove duplicates
    generated_emails = list(set(generated_emails))
    
    print(f"Generated {len(generated_emails)} unique emails")
    
    # Create batch
    batch = EmailBatch(
        user_id=user.id,
        total_emails=len(generated_emails),
        status="processing"
    )
    db.add(batch)
    db.commit()
    
    # Verify emails
    valid_emails = []
    invalid_emails = []
    risky_emails = []
    
    for email in generated_emails:
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
        "total_emails": len(generated_emails),
        "valid_count": len(valid_emails),
        "risky_count": len(risky_emails),
        "invalid_count": len(invalid_emails),
        "categorized_emails": categorized_emails
    }
@app.post("/process-text")
async def process_text_emails(
    request: dict,
    license_key: str,
    db: Session = Depends(get_db)
):
    """Process emails from pasted text"""
    
    user = verify_license(license_key, db)
    
    text = request.get('text', '')
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    # Extract emails from text using multiple patterns
    email_patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        r'\S+@\S+\.\S+'
    ]
    
    emails = []
    for pattern in email_patterns:
        found_emails = re.findall(pattern, text, re.IGNORECASE)
        emails.extend(found_emails)
    
    # Clean and deduplicate
    emails = list(set([email.strip() for email in emails if email.strip()]))
    
    print(f"Text input: {text[:200]}...")
    print(f"Extracted emails: {emails}")
    
    if not emails:
        raise HTTPException(status_code=400, detail="No valid emails found in text")
    
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
        VerifiedEmail.verification_status == 'valid'
    ).all()
    
    if not verified_emails:
        raise HTTPException(status_code=404, detail="No verified emails found")
    
    smtp_config = {
        'server': request.smtp_server or os.getenv('SMTP_SERVER'),
        'port': request.smtp_port or int(os.getenv('SMTP_PORT')),
        'username': request.smtp_username or os.getenv('SMTP_USERNAME'),
        'password': request.smtp_password or os.getenv('SMTP_PASSWORD')
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
    
    try:
        content = await file.read()
        print(f"File: {file.filename}, Size: {len(content)} bytes")
        
        if file.filename.endswith('.pdf'):
            # Extract from PDF with multiple methods
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = ""
                
                # Method 1: Standard extraction
                for page in pdf_reader.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except:
                        continue
                
                # Method 2: If no text, try raw content
                if len(text.strip()) < 10:
                    raw_text = content.decode('utf-8', errors='ignore')
                    text += raw_text
                
                # Method 3: More aggressive email search
                email_patterns = [
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                    r'\S+@\S+\.\S+'
                ]
                
                for pattern in email_patterns:
                    found_emails = re.findall(pattern, text, re.IGNORECASE)
                    emails.extend(found_emails)
                
                print(f"PDF text length: {len(text)}")
                print(f"First 500 chars: {repr(text[:500])}")
                print(f"Emails found: {emails}")
                
            except Exception as e:
                print(f"PDF error: {e}")
                # Fallback: treat as binary and search for email patterns
                try:
                    text = content.decode('latin-1', errors='ignore')
                    fallback_emails = re.findall(r'\S+@\S+\.\S+', text)
                    emails.extend(fallback_emails)
                    print(f"Fallback extraction found: {fallback_emails}")
                except Exception as e2:
                    print(f"Fallback failed: {e2}")
                    
        elif file.filename.endswith(('.csv', '.xlsx', '.xls')):
            # Extract from CSV/Excel without pandas
            try:
                if file.filename.endswith('.csv'):
                    # Simple CSV parsing
                    text = content.decode('utf-8', errors='ignore')
                    lines = text.split('\n')
                    for line in lines:
                        if '@' in line:
                            found_emails = re.findall(r'\S+@\S+\.\S+', line)
                            emails.extend(found_emails)
                else:
                    # Excel parsing with openpyxl
                    from openpyxl import load_workbook
                    wb = load_workbook(io.BytesIO(content))
                    ws = wb.active
                    
                    for row in ws.iter_rows(values_only=True):
                        for cell in row:
                            if cell and '@' in str(cell):
                                if re.match(r'\S+@\S+\.\S+', str(cell)):
                                    emails.append(str(cell))
                                
                print(f"Emails from Excel/CSV: {emails}")
            except Exception as e:
                print(f"Excel/CSV error: {e}")
                            
        else:
            # Extract from text file
            try:
                text = content.decode('utf-8', errors='ignore')
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                print(f"Text file emails: {emails}")
            except Exception as e:
                print(f"Text file error: {e}")
    
    except Exception as e:
        print(f"File processing error: {e}")
    
    # Remove duplicates and clean
    unique_emails = list(set([email.strip() for email in emails if email.strip()]))
    print(f"Final unique emails: {unique_emails}")
    return unique_emails

def verify_license(license_key: str, db: Session) -> User:
    """Verify user license with device binding"""
    user = db.query(User).filter(User.license_key == license_key).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid license key")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="License not activated")
    
    # Auto-renew if expired
    if user.expires_at < datetime.utcnow():
        user.expires_at = datetime.utcnow() + timedelta(days=30)
        db.commit()
    
    # Check device binding
    device_info = f"{platform.system()}-{platform.node()}-{user.email}"
    current_device_hash = hashlib.md5(device_info.encode()).hexdigest()[:8]
    
    if user.device_hash != current_device_hash:
        raise HTTPException(status_code=403, detail="License key bound to different device")
    
    return user

def send_license_email(email: str, license_key: str):
    """Send license key to user email"""
    try:
        msg = MIMEText(f"""
        NEXUS EMAIL VERIFICATION SYSTEM
        
        Your License Key: {license_key}
        
        To activate your account:
        1. Go to http://localhost:8002
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