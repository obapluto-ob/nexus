from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
from datetime import datetime
import asyncio

from database import get_db, engine, Base
from models import Email, Campaign, EmailList
from schemas import EmailCreate, EmailResponse, CampaignCreate, CampaignResponse
from email_verifier import EmailVerifier
from email_sender import EmailSender
from email_collector import EmailCollector

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
except Exception as e:
    print(f"Database error: {e}")

app = FastAPI(
    title="Email Verification & Campaign Tool",
    description="Professional email verification and campaign management system",
    version="1.0.0"
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
email_sender = EmailSender()
email_collector = EmailCollector()

@app.get("/")
async def root():
    return {"message": "Email Verification & Campaign Tool API", "version": "1.0.0"}

@app.post("/emails/collect", response_model=dict)
async def collect_emails(
    sources: List[str],
    keywords: List[str],
    max_emails: int = 10000,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Collect emails from various sources"""
    background_tasks.add_task(
        email_collector.collect_bulk_emails,
        sources, keywords, max_emails, db
    )
    return {"message": f"Email collection started for {max_emails} emails", "status": "processing"}

@app.post("/emails/verify", response_model=dict)
async def verify_emails(
    email_list_id: Optional[int] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Verify emails in bulk"""
    background_tasks.add_task(email_verifier.verify_bulk_emails, email_list_id, db)
    return {"message": "Email verification started", "status": "processing"}

@app.get("/emails/verified", response_model=List[EmailResponse])
async def get_verified_emails(
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get verified emails"""
    emails = db.query(Email).filter(Email.is_verified == True).offset(offset).limit(limit).all()
    return emails

@app.post("/campaigns/create", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    db: Session = Depends(get_db)
):
    """Create a new email campaign"""
    db_campaign = Campaign(**campaign.dict())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@app.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: int,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Send campaign to verified emails"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    background_tasks.add_task(email_sender.send_campaign, campaign_id, db)
    return {"message": "Campaign sending started", "campaign_id": campaign_id}

@app.post("/maps/scrape", response_model=dict)
async def scrape_google_maps(
    query: str = None,
    location: str = None,
    max_results: int = 50,
    auto_mode: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Scrape Google Maps for business emails with smart search management"""
    from simple_scraper import SimpleEmailScraper
    from smart_search_manager import SmartSearchManager
    
    search_manager = SmartSearchManager()
    scraper = SimpleEmailScraper()
    
    if auto_mode:
        # Auto mode: get next best searches
        next_searches = search_manager.get_next_searches(5)
        all_results = []
        total_saved = 0
        
        for search_item in next_searches:
            try:
                businesses = scraper.scrape_businesses_with_emails(
                    search_item['query'], 
                    search_item['location'], 
                    max_results
                )
                
                # Save emails to database
                saved_count = 0
                for business in businesses:
                    for email in business['emails']:
                        try:
                            existing_email = db.query(Email).filter(Email.email_address == email).first()
                            if not existing_email:
                                email_obj = Email(
                                    email_address=email,
                                    company=business['name'],
                                    source=f"auto_search:{search_item['query']}",
                                )
                                db.add(email_obj)
                                saved_count += 1
                        except:
                            continue
                
                db.commit()
                total_saved += saved_count
                
                # Mark search as completed
                search_manager.mark_search_completed(
                    search_item['query'], 
                    search_item['location'], 
                    len(businesses)
                )
                
                all_results.extend(businesses)
                
            except Exception as e:
                search_manager.mark_search_failed(
                    search_item['query'], 
                    search_item['location'], 
                    str(e)
                )
        
        return {
            "message": "Auto search completed",
            "searches_performed": len(next_searches),
            "businesses_found": len(all_results),
            "emails_saved": total_saved,
            "search_stats": search_manager.get_search_stats()
        }
    
    else:
        # Manual mode: use provided query and location
        if not query:
            query = "financial advisor"
        if not location:
            location = "New York"
        
        # Check if already completed
        if search_manager.is_search_completed(query, location):
            return {
                "message": "Search already completed",
                "query": query,
                "location": location,
                "suggestion": "Try auto_mode=true for new searches"
            }
        
        try:
            businesses = scraper.scrape_businesses_with_emails(query, location, max_results)
            
            # Save emails to database
            saved_count = 0
            for business in businesses:
                for email in business['emails']:
                    try:
                        existing_email = db.query(Email).filter(Email.email_address == email).first()
                        if not existing_email:
                            email_obj = Email(
                                email_address=email,
                                company=business['name'],
                                source=f"manual_search:{query}",
                            )
                            db.add(email_obj)
                            saved_count += 1
                    except:
                        continue
            
            db.commit()
            
            # Mark search as completed
            search_manager.mark_search_completed(query, location, len(businesses))
            
            return {
                "message": "Manual search completed",
                "businesses_found": len(businesses),
                "emails_saved": saved_count,
                "businesses": businesses[:10]  # Show first 10
            }
            
        except Exception as e:
            search_manager.mark_search_failed(query, location, str(e))
            return {
                "message": "Search failed",
                "error": str(e),
                "query": query,
                "location": location
            }

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        total_emails = db.query(Email).count()
        verified_emails = db.query(Email).filter(Email.is_verified == True).count()
        campaigns = db.query(Campaign).count()
        
        return {
            "total_emails": total_emails,
            "verified_emails": verified_emails,
            "verification_rate": (verified_emails / total_emails * 100) if total_emails > 0 else 0,
            "total_campaigns": campaigns
        }
    except Exception as e:
        return {
            "total_emails": 0,
            "verified_emails": 0,
            "verification_rate": 0,
            "total_campaigns": 0
        }

@app.get("/search/options")
async def get_search_options():
    """Get available search options for dropdowns"""
    from smart_search_manager import SmartSearchManager
    
    manager = SmartSearchManager()
    
    return {
        "business_types": manager.get_business_queries(),
        "locations": manager.get_major_cities(),
        "recommended_combinations": [
            {"query": "hedge fund", "location": "New York", "priority": "High"},
            {"query": "investment banking", "location": "London", "priority": "High"},
            {"query": "private equity", "location": "Singapore", "priority": "High"},
            {"query": "asset management", "location": "Hong Kong", "priority": "High"},
            {"query": "financial advisor", "location": "Chicago", "priority": "Medium"},
            {"query": "wealth management", "location": "Toronto", "priority": "Medium"}
        ]
    }

@app.get("/search/next")
async def get_next_searches():
    """Get next recommended searches"""
    from smart_search_manager import SmartSearchManager
    
    manager = SmartSearchManager()
    next_searches = manager.get_next_searches(10)
    stats = manager.get_search_stats()
    top_performers = manager.get_top_performing_searches(5)
    
    return {
        "next_searches": next_searches,
        "stats": stats,
        "top_performers": top_performers
    }
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)