import requests
from bs4 import BeautifulSoup
import re
from typing import Set, List, Dict
import time
import json
from urllib.parse import urljoin, urlparse

class MegaEmailFinder:
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def find_emails_for_company(self, company_name: str, domain: str = None) -> Dict:
        """Master function to find emails using all free methods"""
        all_emails = set()
        sources = {}
        
        # Method 1: Company website scraping
        if domain:
            website_emails = self.scrape_company_website(domain)
            all_emails.update(website_emails)
            sources['website'] = list(website_emails)
        
        # Method 2: Google dorking
        google_emails = self.google_dork_search(company_name, domain)
        all_emails.update(google_emails)
        sources['google'] = list(google_emails)
        
        # Method 3: Social media scraping
        social_emails = self.scrape_social_platforms(company_name)
        all_emails.update(social_emails)
        sources['social'] = list(social_emails)
        
        # Method 4: Business directories
        directory_emails = self.scrape_directories(company_name)
        all_emails.update(directory_emails)
        sources['directories'] = list(directory_emails)
        
        # Method 5: News articles and press releases
        news_emails = self.scrape_news_mentions(company_name)
        all_emails.update(news_emails)
        sources['news'] = list(news_emails)
        
        return {
            'total_emails': len(all_emails),
            'emails': list(all_emails),
            'sources': sources
        }
    
    def scrape_company_website(self, domain: str) -> Set[str]:
        """Deep scrape company website"""
        emails = set()
        base_url = f"https://{domain}"
        
        # Common pages that contain emails
        pages = [
            '/', '/contact', '/about', '/team', '/staff', '/leadership',
            '/contact-us', '/about-us', '/management', '/executives',
            '/press', '/media', '/investor-relations', '/careers'
        ]
        
        for page in pages:
            try:
                url = urljoin(base_url, page)
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract emails from text
                    text = soup.get_text()
                    found_emails = self.email_pattern.findall(text)
                    emails.update(found_emails)
                    
                    # Check mailto links
                    for link in soup.find_all('a', href=True):
                        if 'mailto:' in link['href']:
                            email = link['href'].replace('mailto:', '').split('?')[0]
                            if self.email_pattern.match(email):
                                emails.add(email)
                
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                continue
        
        return emails
    
    def google_dork_search(self, company: str, domain: str = None) -> Set[str]:
        """Advanced Google search for emails"""
        emails = set()
        
        # Google search queries
        queries = [
            f'"{company}" email contact',
            f'"{company}" "@" -site:linkedin.com -site:facebook.com',
            f'"{company}" "contact us" email',
            f'"{company}" "press contact" email',
            f'"{company}" CEO email',
            f'"{company}" sales email',
            f'"{company}" support email'
        ]
        
        if domain:
            queries.extend([
                f'site:{domain} email',
                f'site:{domain} contact',
                f'site:{domain} "@"'
            ])
        
        for query in queries:
            try:
                search_url = f"https://www.google.com/search?q={query}&num=20"
                response = requests.get(search_url, headers=self.headers)
                
                if response.status_code == 200:
                    found_emails = self.email_pattern.findall(response.text)
                    emails.update(found_emails)
                
                time.sleep(2)  # Respect rate limits
                
            except Exception as e:
                continue
        
        return emails
    
    def scrape_social_platforms(self, company: str) -> Set[str]:
        """Scrape social media platforms"""
        emails = set()
        
        # Social media URLs to check
        social_urls = [
            f"https://www.facebook.com/{company.lower().replace(' ', '').replace('.', '')}",
            f"https://twitter.com/{company.lower().replace(' ', '').replace('.', '')}",
            f"https://www.instagram.com/{company.lower().replace(' ', '').replace('.', '')}",
        ]
        
        for url in social_urls:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    found_emails = self.email_pattern.findall(response.text)
                    emails.update(found_emails)
                time.sleep(1)
            except:
                continue
        
        return emails
    
    def scrape_directories(self, company: str) -> Set[str]:
        """Scrape business directories"""
        emails = set()
        
        # Business directory searches
        directory_searches = [
            f"https://www.yellowpages.com/search?search_terms={company.replace(' ', '+')}",
            f"https://www.yelp.com/search?find_desc={company.replace(' ', '+')}",
            f"https://www.bbb.org/search?find_country=USA&find_text={company.replace(' ', '+')}",
        ]
        
        for url in directory_searches:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    found_emails = self.email_pattern.findall(response.text)
                    emails.update(found_emails)
                time.sleep(1)
            except:
                continue
        
        return emails
    
    def scrape_news_mentions(self, company: str) -> Set[str]:
        """Find emails in news articles and press releases"""
        emails = set()
        
        # News search queries
        news_queries = [
            f'"{company}" press release contact',
            f'"{company}" media contact email',
            f'"{company}" spokesperson email'
        ]
        
        for query in news_queries:
            try:
                search_url = f"https://www.google.com/search?q={query}&tbm=nws"
                response = requests.get(search_url, headers=self.headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Get article links
                    for link in soup.find_all('a', href=True):
                        if 'http' in link['href'] and 'google' not in link['href']:
                            try:
                                article_response = requests.get(link['href'], headers=self.headers, timeout=5)
                                found_emails = self.email_pattern.findall(article_response.text)
                                emails.update(found_emails)
                                time.sleep(0.5)
                            except:
                                continue
                
                time.sleep(2)
                
            except Exception as e:
                continue
        
        return emails
    
    def generate_email_variations(self, names: List[str], domain: str) -> Set[str]:
        """Generate common email patterns for verification"""
        emails = set()
        
        common_patterns = [
            "{first}@{domain}",
            "{first}.{last}@{domain}",
            "{first}_{last}@{domain}",
            "{first}{last}@{domain}",
            "{last}@{domain}",
            "{first}{last[0]}@{domain}",
            "{first[0]}{last}@{domain}",
            "{first[0]}.{last}@{domain}"
        ]
        
        generic_emails = [
            f"info@{domain}",
            f"contact@{domain}",
            f"sales@{domain}",
            f"support@{domain}",
            f"hello@{domain}",
            f"admin@{domain}",
            f"team@{domain}"
        ]
        
        emails.update(generic_emails)
        
        for name in names:
            parts = name.lower().strip().split()
            if len(parts) >= 2:
                first, last = parts[0], parts[-1]
                for pattern in common_patterns:
                    try:
                        email = pattern.format(first=first, last=last, domain=domain)
                        emails.add(email)
                    except:
                        continue
        
        return emails

# Usage example
if __name__ == "__main__":
    finder = MegaEmailFinder()
    
    # Find emails for a trading company
    results = finder.find_emails_for_company("Goldman Sachs", "goldmansachs.com")
    
    print(f"Found {results['total_emails']} emails:")
    for email in results['emails']:
        print(f"  - {email}")
    
    print(f"\nSources breakdown:")
    for source, emails in results['sources'].items():
        print(f"  {source}: {len(emails)} emails")