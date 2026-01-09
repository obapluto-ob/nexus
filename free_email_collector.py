import requests
from bs4 import BeautifulSoup
import re
from typing import Set, List, Dict
import time
import json

class FreeEmailCollector:
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
    def scrape_company_website(self, domain: str) -> Set[str]:
        """Scrape company website for emails"""
        emails = set()
        pages_to_check = [
            f"https://{domain}",
            f"https://{domain}/contact",
            f"https://{domain}/about",
            f"https://{domain}/team",
            f"https://{domain}/staff",
            f"https://{domain}/leadership"
        ]
        
        for url in pages_to_check:
            try:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text()
                found_emails = self.email_pattern.findall(text)
                emails.update(found_emails)
                time.sleep(1)
            except:
                continue
        return emails
    
    def search_google_dorks(self, company: str) -> Set[str]:
        """Use Google search operators to find emails"""
        emails = set()
        search_queries = [
            f'"{company}" email contact',
            f'site:{company.lower().replace(" ", "")}.com email',
            f'"{company}" "@" contact',
            f'"{company}" "email" "contact us"'
        ]
        
        for query in search_queries:
            try:
                # Note: Be careful with Google rate limits
                search_url = f"https://www.google.com/search?q={query}"
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                response = requests.get(search_url, headers=headers)
                found_emails = self.email_pattern.findall(response.text)
                emails.update(found_emails)
                time.sleep(2)  # Respect rate limits
            except:
                continue
        return emails
    
    def scrape_social_media(self, company: str) -> Set[str]:
        """Scrape social media for contact info"""
        emails = set()
        # Facebook, Twitter pages often have contact emails
        social_urls = [
            f"https://www.facebook.com/{company.lower().replace(' ', '')}",
            f"https://twitter.com/{company.lower().replace(' ', '')}"
        ]
        
        for url in social_urls:
            try:
                response = requests.get(url, timeout=10)
                found_emails = self.email_pattern.findall(response.text)
                emails.update(found_emails)
                time.sleep(1)
            except:
                continue
        return emails
    
    def scrape_business_directories(self, company: str) -> Set[str]:
        """Scrape business directories"""
        emails = set()
        directories = [
            f"https://www.yellowpages.com/search?search_terms={company}",
            f"https://www.yelp.com/search?find_desc={company}",
        ]
        
        for url in directories:
            try:
                response = requests.get(url, timeout=10)
                found_emails = self.email_pattern.findall(response.text)
                emails.update(found_emails)
                time.sleep(1)
            except:
                continue
        return emails
    
    def generate_common_emails(self, domain: str, names: List[str]) -> Set[str]:
        """Generate common email patterns"""
        emails = set()
        patterns = [
            "{first}@{domain}",
            "{first}.{last}@{domain}",
            "{first}_{last}@{domain}",
            "{first}{last}@{domain}",
            "{last}@{domain}",
            "info@{domain}",
            "contact@{domain}",
            "sales@{domain}",
            "support@{domain}",
            "admin@{domain}"
        ]
        
        for name in names:
            parts = name.lower().split()
            if len(parts) >= 2:
                first, last = parts[0], parts[-1]
                for pattern in patterns:
                    email = pattern.format(first=first, last=last, domain=domain)
                    emails.add(email)
        
        return emails