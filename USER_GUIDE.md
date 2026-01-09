# Email Tool - User Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Setup
```bash
# Install ChromeDriver (for Google Maps)
python setup_chrome.py

# Start the tool
python main.py
```

### Step 2: Access Tool
- Open browser: `http://localhost:8001`
- API docs: `http://localhost:8001/docs`

### Step 3: Configure Email Sending (Optional)
Edit `.env` file:
```
SMTP_USERNAME=your_gmail@gmail.com
SMTP_PASSWORD=your_app_password
```

## 📧 How Users Collect 1M+ Emails

### Method 1: Google Maps (BEST - No APIs needed)
1. Go to "Google Maps" tab
2. Enter: "financial advisor" 
3. Location: "New York"
4. Max Results: 100
5. Click "Start Scraping"

**Result: 50-100 verified business emails per search**

### Method 2: Website Scraping
1. Go to "Collect Emails" tab
2. Add websites (one per line):
   ```
   https://tradingfirm.com
   https://investmentcompany.com
   ```
3. Keywords: "trading, finance"
4. Click "Start Collection"

### Method 3: CSV Upload
1. Prepare CSV with email column
2. Add file path in sources:
   ```
   C:\path\to\emails.csv
   ```

## ✅ Email Verification
1. Go to "Verify Emails" tab
2. Click "Start Verification"
3. Tool checks:
   - Email format
   - Domain exists
   - Mailbox exists
   - Not disposable/spam

## 📨 Send Campaigns
1. Go to "Create Campaign" tab
2. Fill campaign details:
   - Name: "Trading Newsletter"
   - Subject: "Hi {{first_name}}, exclusive trading tips"
   - Content: Personalized message
3. Click "Create & Send"

## 🎯 Best Searches for Trading Business

**Google Maps Queries:**
- "financial advisor" + city
- "investment firm" + city
- "trading company" + city
- "wealth management" + city
- "forex broker" + city
- "hedge fund" + city

**Each search = 50-200 emails**
**10 cities × 6 queries = 3,000-12,000 emails**

## 💰 Monetization for Others

### Option 1: SaaS Model
- Charge $50/month for unlimited scraping
- $100/month for verification + sending
- $200/month for white-label version

### Option 2: Service Model
- Charge $0.10 per verified email
- $500 for 10K verified emails
- $2000 for 50K verified emails

### Option 3: API Access
- $0.05 per API call
- Bulk pricing for resellers

## 🔧 Technical Requirements

**Minimum:**
- Python 3.8+
- 4GB RAM
- Chrome browser

**For 1M+ emails:**
- 16GB RAM
- PostgreSQL database
- VPS/dedicated server

## 📊 Expected Results

**Per Day (manual):** 1,000-5,000 emails
**Per Day (automated):** 10,000-50,000 emails
**Per Month:** 100K-1M+ emails

**Verification Rate:** 70-85%
**Deliverability:** 90%+ for verified emails