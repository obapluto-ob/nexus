from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr

class EmailVerifyRequest(BaseModel):
    emails: List[EmailStr]

class CampaignSendRequest(BaseModel):
    batch_id: int
    subject: str
    content: str
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    license_key: str
    is_active: bool
    created_at: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True

class EmailBatchResponse(BaseModel):
    id: int
    total_emails: int
    verified_count: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True