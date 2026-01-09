import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import asyncio
from typing import List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from models import Campaign, Email, CampaignSend
import os
from jinja2 import Template

class EmailSender:
    def __init__(self):
        self.smtp_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'smtp_username': os.getenv('SMTP_USERNAME'),
            'smtp_password': os.getenv('SMTP_PASSWORD'),
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        }
    
    def create_smtp_connection(self):
        """Create SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
            
            if self.smtp_config['use_tls']:
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            server.login(self.smtp_config['smtp_username'], self.smtp_config['smtp_password'])
            return server
        except Exception as e:
            print(f"SMTP connection error: {str(e)}")
            return None
    
    def personalize_content(self, content: str, email_data: Dict) -> str:
        """Personalize email content with recipient data"""
        template = Template(content)
        return template.render(
            first_name=email_data.get('first_name', ''),
            last_name=email_data.get('last_name', ''),
            company=email_data.get('company', ''),
            email=email_data.get('email', '')
        )
    
    def create_email_message(self, campaign: Campaign, recipient: Email) -> MIMEMultipart:
        """Create email message"""
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{campaign.sender_name} <{campaign.sender_email}>"
        msg['To'] = recipient.email_address
        msg['Subject'] = campaign.subject
        
        # Personalize content
        recipient_data = {
            'first_name': recipient.first_name or '',
            'last_name': recipient.last_name or '',
            'company': recipient.company or '',
            'email': recipient.email_address
        }
        
        personalized_content = self.personalize_content(campaign.content, recipient_data)
        
        # Create HTML and text versions
        html_content = f"""
        <html>
            <body>
                {personalized_content.replace(chr(10), '<br>')}
                <br><br>
                <small>
                    <a href="{{{{ unsubscribe_url }}}}">Unsubscribe</a> | 
                    <img src="{{{{ tracking_pixel }}}}" width="1" height="1" />
                </small>
            </body>
        </html>
        """
        
        text_content = personalized_content
        
        # Attach parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        return msg
    
    async def send_single_email(self, campaign: Campaign, recipient: Email, server: smtplib.SMTP) -> bool:
        """Send single email"""
        try:
            msg = self.create_email_message(campaign, recipient)
            server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error sending email to {recipient.email_address}: {str(e)}")
            return False
    
    async def send_campaign(self, campaign_id: int, db: Session):
        """Send campaign to all verified emails"""
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return
        
        # Get verified emails
        verified_emails = db.query(Email).filter(
            Email.is_verified == True,
            Email.verification_status == 'valid'
        ).all()
        
        campaign.status = 'sending'
        campaign.total_recipients = len(verified_emails)
        campaign.sent_at = datetime.utcnow()
        db.commit()
        
        # Create SMTP connection
        server = self.create_smtp_connection()
        if not server:
            campaign.status = 'failed'
            db.commit()
            return
        
        sent_count = 0
        batch_size = 100  # Send in batches to avoid overwhelming SMTP server
        
        try:
            for i in range(0, len(verified_emails), batch_size):
                batch = verified_emails[i:i + batch_size]
                
                for email in batch:
                    # Check if already sent
                    existing_send = db.query(CampaignSend).filter(
                        CampaignSend.campaign_id == campaign_id,
                        CampaignSend.email_id == email.id
                    ).first()
                    
                    if existing_send:
                        continue
                    
                    # Send email
                    success = await self.send_single_email(campaign, email, server)
                    
                    # Record send attempt
                    campaign_send = CampaignSend(
                        campaign_id=campaign_id,
                        email_id=email.id,
                        status='sent' if success else 'failed',
                        sent_at=datetime.utcnow() if success else None
                    )
                    db.add(campaign_send)
                    
                    if success:
                        sent_count += 1
                    
                    # Small delay between emails
                    await asyncio.sleep(0.1)
                
                # Update campaign progress
                campaign.sent_count = sent_count
                db.commit()
                
                # Longer delay between batches
                await asyncio.sleep(5)
        
        finally:
            server.quit()
            campaign.status = 'completed'
            campaign.sent_count = sent_count
            db.commit()
    
    def get_campaign_stats(self, campaign_id: int, db: Session) -> Dict:
        """Get campaign statistics"""
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {}
        
        sends = db.query(CampaignSend).filter(CampaignSend.campaign_id == campaign_id).all()
        
        stats = {
            'total_recipients': campaign.total_recipients,
            'sent_count': len([s for s in sends if s.status == 'sent']),
            'failed_count': len([s for s in sends if s.status == 'failed']),
            'opened_count': len([s for s in sends if s.opened_at is not None]),
            'clicked_count': len([s for s in sends if s.clicked_at is not None]),
            'delivery_rate': 0,
            'open_rate': 0,
            'click_rate': 0
        }
        
        if stats['sent_count'] > 0:
            stats['delivery_rate'] = (stats['sent_count'] / campaign.total_recipients) * 100
            stats['open_rate'] = (stats['opened_count'] / stats['sent_count']) * 100
            stats['click_rate'] = (stats['clicked_count'] / stats['sent_count']) * 100
        
        return stats