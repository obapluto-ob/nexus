from celery_app import celery_app
from database import SessionLocal
from email_collector import EmailCollector
from email_verifier import EmailVerifier
from email_sender import EmailSender
from google_maps_scraper import GoogleMapsScraper
from models import Email

@celery_app.task
def collect_emails_task(sources, keywords, max_emails):
    """Background task for email collection"""
    db = SessionLocal()
    try:
        collector = EmailCollector()
        result = collector.collect_bulk_emails(sources, keywords, max_emails, db)
        return {"status": "completed", "message": f"Collected emails from {len(sources)} sources"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task
def verify_emails_task(email_list_id=None):
    """Background task for email verification"""
    db = SessionLocal()
    try:
        verifier = EmailVerifier()
        result = verifier.verify_bulk_emails(email_list_id, db)
        return {"status": "completed", "message": "Email verification completed"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task
def send_campaign_task(campaign_id):
    """Background task for sending campaigns"""
    db = SessionLocal()
    try:
        sender = EmailSender()
        result = sender.send_campaign(campaign_id, db)
        return {"status": "completed", "message": f"Campaign {campaign_id} sent"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task
def scrape_google_maps_task(query, location, max_results):
    """Background task for Google Maps scraping"""
    db = SessionLocal()
    try:
        scraper = GoogleMapsScraper()
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
                            source=f"google_maps:{query}",
                        )
                        db.add(email_obj)
                        saved_count += 1
                except:
                    continue
        
        db.commit()
        return {
            "status": "completed", 
            "businesses_found": len(businesses),
            "emails_saved": saved_count
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()