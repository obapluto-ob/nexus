import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Set
from urllib.parse import urljoin

class SimpleEmailScraper:
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_website_for_emails(self, url: str) -> Set[str]:
        """Scrape a single website for emails"""
        emails = set()
        try:
            if not url.startswith('http'):
                url = 'https://' + url
            
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract from text
                text = soup.get_text()
                found_emails = self.email_pattern.findall(text)
                emails.update(found_emails)
                
                # Check mailto links
                for link in soup.find_all('a', href=True):
                    if 'mailto:' in link['href']:
                        email = link['href'].replace('mailto:', '').split('?')[0]
                        if self.email_pattern.match(email):
                            emails.add(email)
                
                # Check common pages
                common_pages = ['/contact', '/about', '/team']
                for page in common_pages:
                    try:
                        page_url = urljoin(url, page)
                        page_response = requests.get(page_url, headers=self.headers, timeout=5)
                        if page_response.status_code == 200:
                            page_soup = BeautifulSoup(page_response.content, 'html.parser')
                            page_text = page_soup.get_text()
                            page_emails = self.email_pattern.findall(page_text)
                            emails.update(page_emails)
                        time.sleep(0.5)
                    except:
                        continue
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        
        return emails
    
    def search_google_for_businesses(self, query: str, location: str = "") -> List[Dict]:
        """Search Google for business websites"""
        businesses = []
        try:
            search_query = f"{query} {location} site:*.com OR site:*.org OR site:*.net"
            search_url = f"https://www.google.com/search?q={search_query}&num=50"
            
            response = requests.get(search_url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract search result links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/url?q=' in href and 'google' not in href:
                    try:
                        url = href.split('/url?q=')[1].split('&')[0]
                        if url.startswith('http') and any(domain in url for domain in ['.com', '.org', '.net']):
                            # Extract title
                            title_elem = link.find('h3')
                            title = title_elem.text if title_elem else url
                            
                            businesses.append({
                                'name': title,
                                'website': url,
                                'query': query,
                                'location': location
                            })
                    except:
                        continue
            
        except Exception as e:
            print(f"Google search error: {e}")
        
        return businesses[:20]  # Limit results
    
    def scrape_businesses_with_emails(self, query: str, location: str = "", max_results: int = 20) -> List[Dict]:
        """Find businesses and extract their emails"""
        print(f"Searching for '{query}' in '{location}'...")
        
        # Get businesses from Google search
        businesses = self.search_google_for_businesses(query, location)
        print(f"Found {len(businesses)} businesses")
        
        # Extract emails from each business
        results = []
        for i, business in enumerate(businesses[:max_results]):
            print(f"Processing {i+1}/{len(businesses)}: {business['name']}")
            
            emails = self.scrape_website_for_emails(business['website'])
            business['emails'] = list(emails)
            business['email_count'] = len(emails)
            
            if emails:  # Only keep businesses with emails
                results.append(business)
            
            time.sleep(1)  # Rate limiting
        
        print(f"Found emails for {len(results)} businesses")
        return results

# Test the scraper
if __name__ == "__main__":
    scraper = SimpleEmailScraper()
    
    # Test with a simple search
    results = scraper.scrape_businesses_with_emails("financial advisor", "New York")
    
    for business in results:
        print(f"\n{business['name']}")
        print(f"Website: {business['website']}")
        print(f"Emails: {', '.join(business['emails'])}")