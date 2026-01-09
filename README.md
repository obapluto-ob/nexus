# Email Verification & Campaign Tool

A powerful, professional-grade email verification and campaign management system designed for trading businesses and marketing professionals.

## Features

### 🔍 Email Collection
- **Web Scraping**: Extract emails from websites automatically
- **API Integrations**: Hunter.io, Apollo.io, LinkedIn Sales Navigator
- **CSV Import**: Bulk import from spreadsheets
- **Google Search**: Find emails through targeted searches
- **Multi-source Collection**: Combine multiple sources for maximum coverage

### ✅ Email Verification
- **Format Validation**: RFC-compliant email format checking
- **MX Record Verification**: DNS-based domain validation
- **SMTP Verification**: Real-time mailbox existence checking
- **Disposable Email Detection**: Filter out temporary email services
- **Role-based Email Detection**: Identify generic business emails
- **Bulk Processing**: Verify thousands of emails efficiently

### 📧 Campaign Management
- **Personalized Campaigns**: Dynamic content with recipient data
- **Template System**: Jinja2-powered email templates
- **Batch Sending**: Rate-limited, respectful email delivery
- **Tracking & Analytics**: Open rates, click rates, delivery stats
- **SMTP Integration**: Works with Gmail, Outlook, custom SMTP servers

### 🚀 API-First Design
- **RESTful API**: Complete programmatic access
- **Web Interface**: User-friendly dashboard
- **Background Processing**: Async task handling
- **Database Support**: SQLite, PostgreSQL, MySQL
- **Scalable Architecture**: Ready for high-volume operations

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd 100_dollarsdaily

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env` file and configure your settings:

```bash
# Database (SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite:///./email_tool.db

# SMTP Settings (for sending campaigns)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# API Keys (optional, for enhanced collection)
HUNTER_API_KEY=your_hunter_io_key
APOLLO_API_KEY=your_apollo_io_key
```

### 3. Run the Application

```bash
# Start the API server
python main.py

# Access the web interface
# Open http://localhost:8000 in your browser
```

## Usage Guide

### Email Collection

#### Method 1: Web Interface
1. Go to "Collect Emails" tab
2. Add sources (websites, CSV files, API endpoints)
3. Set keywords and maximum email count
4. Click "Start Collection"

#### Method 2: API
```python
import requests

response = requests.post('http://localhost:8000/emails/collect', json={
    'sources': ['https://example.com', 'hunter:company.com'],
    'keywords': ['trading', 'finance'],
    'max_emails': 10000
})
```

### Email Verification

#### Bulk Verification
```python
# Verify all unverified emails
response = requests.post('http://localhost:8000/emails/verify')

# Get verification results
verified_emails = requests.get('http://localhost:8000/emails/verified')
```

### Campaign Creation & Sending

```python
# Create campaign
campaign_data = {
    'name': 'Trading Newsletter Q1',
    'subject': 'Exclusive Trading Insights for {{ first_name }}',
    'sender_name': 'John Trader',
    'sender_email': 'john@tradingfirm.com',
    'content': '''
    Hi {{ first_name }},
    
    I hope this email finds you well. As a professional in {{ company }}, 
    you might be interested in our latest trading strategies...
    
    Best regards,
    {{ sender_name }}
    '''
}

campaign = requests.post('http://localhost:8000/campaigns/create', json=campaign_data)

# Send campaign
requests.post(f'http://localhost:8000/campaigns/{campaign.json()["id"]}/send')
```

## Advanced Configuration

### Database Setup (Production)

For production use, configure PostgreSQL:

```bash
# Install PostgreSQL
# Create database: email_tool
# Update .env:
DATABASE_URL=postgresql://username:password@localhost/email_tool
```

### SMTP Configuration

#### Gmail Setup
1. Enable 2-factor authentication
2. Generate app password
3. Use app password in SMTP_PASSWORD

#### Custom SMTP
```env
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587
SMTP_USERNAME=campaigns@yourdomain.com
SMTP_PASSWORD=your_password
```

### API Keys Setup

#### Hunter.io
1. Sign up at hunter.io
2. Get API key from dashboard
3. Add to HUNTER_API_KEY in .env

#### Apollo.io
1. Sign up at apollo.io
2. Get API key from settings
3. Add to APOLLO_API_KEY in .env

## Scaling for 1M+ Emails

### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX idx_email_verified ON emails(is_verified);
CREATE INDEX idx_email_status ON emails(verification_status);
CREATE INDEX idx_email_created ON emails(created_at);
```

### Background Processing
```bash
# Install Redis for task queue
pip install redis celery

# Start Celery worker
celery -A main worker --loglevel=info
```

### Rate Limiting
- Verification: 100 emails/minute (configurable)
- Sending: 50 emails/minute (configurable)
- Collection: Respects robots.txt and rate limits

## API Documentation

### Endpoints

#### Email Collection
- `POST /emails/collect` - Start email collection
- `GET /emails/verified` - Get verified emails
- `GET /stats` - Get system statistics

#### Campaign Management
- `POST /campaigns/create` - Create new campaign
- `POST /campaigns/{id}/send` - Send campaign
- `GET /campaigns/{id}/stats` - Get campaign statistics

#### Verification
- `POST /emails/verify` - Start bulk verification
- `GET /emails/{id}` - Get single email details

## Best Practices

### Legal Compliance
- Always comply with CAN-SPAM Act
- Include unsubscribe links
- Respect opt-out requests
- Follow GDPR guidelines for EU contacts

### Deliverability
- Warm up new sending domains
- Monitor sender reputation
- Use proper SPF/DKIM records
- Segment your email lists

### Performance
- Use batch processing for large operations
- Implement proper error handling
- Monitor API rate limits
- Regular database maintenance

## Troubleshooting

### Common Issues

#### SMTP Authentication Failed
- Check username/password
- Enable "Less secure apps" for Gmail
- Use app passwords for 2FA accounts

#### Low Verification Rates
- Check internet connection
- Verify DNS settings
- Some servers block verification attempts

#### Slow Performance
- Add database indexes
- Use Redis for caching
- Implement connection pooling

## Support & Customization

This tool is designed to be:
- **Customizable**: Modify collection sources and verification rules
- **Extensible**: Add new APIs and integrations
- **Scalable**: Handle millions of emails with proper setup
- **Professional**: Enterprise-ready with proper error handling

For custom development or enterprise features, the codebase is well-structured and documented for easy modification.

## License

This project is designed for legitimate business use. Please ensure compliance with all applicable laws and regulations regarding email marketing and data collection.