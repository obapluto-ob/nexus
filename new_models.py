from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    license_key = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    device_hash = Column(String)  # Device fingerprint to prevent sharing
    expires_at = Column(DateTime)
    
    # Relationships
    email_batches = relationship("EmailBatch", back_populates="user")

class EmailBatch(Base):
    __tablename__ = "email_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_emails = Column(Integer, default=0)
    verified_count = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="email_batches")
    verified_emails = relationship("VerifiedEmail", back_populates="batch")

class VerifiedEmail(Base):
    __tablename__ = "verified_emails"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("email_batches.id"))
    email_address = Column(String, nullable=False)
    is_valid = Column(Boolean, default=False)
    verification_status = Column(String)  # valid, invalid, risky, unknown
    verified_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    batch = relationship("EmailBatch", back_populates="verified_emails")