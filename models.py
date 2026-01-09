from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    email_address = Column(String, unique=True, index=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_status = Column(String, default="pending")  # pending, valid, invalid, risky
    source = Column(String)  # where the email was collected from
    first_name = Column(String)
    last_name = Column(String)
    company = Column(String)
    industry = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)
    
    # Relationships
    campaign_sends = relationship("CampaignSend", back_populates="email")

class EmailList(Base):
    __tablename__ = "email_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    total_emails = Column(Integer, default=0)
    verified_emails = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sender_name = Column(String, nullable=False)
    sender_email = Column(String, nullable=False)
    status = Column(String, default="draft")  # draft, sending, completed, paused
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    
    # Relationships
    campaign_sends = relationship("CampaignSend", back_populates="campaign")

class CampaignSend(Base):
    __tablename__ = "campaign_sends"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    email_id = Column(Integer, ForeignKey("emails.id"))
    status = Column(String, default="pending")  # pending, sent, failed, opened, clicked
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="campaign_sends")
    email = relationship("Email", back_populates="campaign_sends")