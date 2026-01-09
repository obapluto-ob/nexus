from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class EmailBase(BaseModel):
    email_address: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    source: Optional[str] = None

class EmailCreate(EmailBase):
    pass

class EmailResponse(EmailBase):
    id: int
    is_verified: bool
    verification_status: str
    created_at: datetime
    verified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CampaignBase(BaseModel):
    name: str
    subject: str
    content: str
    sender_name: str
    sender_email: EmailStr

class CampaignCreate(CampaignBase):
    pass

class CampaignResponse(CampaignBase):
    id: int
    status: str
    total_recipients: int
    sent_count: int
    opened_count: int
    clicked_count: int
    created_at: datetime
    sent_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EmailListBase(BaseModel):
    name: str
    description: Optional[str] = None

class EmailListCreate(EmailListBase):
    pass

class EmailListResponse(EmailListBase):
    id: int
    total_emails: int
    verified_emails: int
    created_at: datetime
    
    class Config:
        from_attributes = True