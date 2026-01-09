from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Set

class GoogleMapsScraper:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
    def search_google_maps(self, query: str, location: str = "", max_results: int = 100) -> List[Dict]:
        """Search Google Maps for businesses"""
        businesses = []
        driver = None
        
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            
            # Search Google Maps
            search_query = f"{query} {location}".strip()
            maps_url = f"https://www.google.com/maps/search/{search_query}"
            driver.get(maps_url)
            
            # Wait for results to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-result-index]"))
            )
            
            # Scroll to load more results
            for i in range(5):  # Scroll 5 times to get more results
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Extract business info
            business_elements = driver.find_elements(By.CSS_SELECTOR, "[data-result-index]")
            
            for element in business_elements[:max_results]:
                try:
                    # Click on business to get details
                    element.click()
                    time.sleep(2)
                    
                    # Extract business name
                    name_elem = driver.find_element(By.CSS_SELECTOR, "h1")
                    business_name = name_elem.text if name_elem else ""
                    
                    # Extract website
                    website = ""
                    try:
                        website_elem = driver.find_element(By.CSS_SELECTOR, "[data-item-id='authority'] a")
                        website = website_elem.get_attribute('href')
                    except:
                        pass
                    
                    # Extract phone
                    phone = ""
                    try:
                        phone_elem = driver.find_element(By.CSS_SELECTOR, "[data-item-id*='phone'] span")
                        phone = phone_elem.text
                    except:
                        pass
                    
                    # Extract address
                    address = ""
                    try:
                        address_elem = driver.find_element(By.CSS_SELECTOR, "[data-item-id='address'] span")
                        address = address_elem.text
                    except:
                        pass
                    
                    business_data = {
                        'name': business_name,
                        'website': website,
                        'phone': phone,
                        'address': address,
                        'query': query,
                        'location': location
                    }
                    
                    businesses.append(business_data)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Google Maps scraping error: {e}")
        finally:
            if driver:
                driver.quit()
                
        return businesses
    
    def extract_emails_from_website(self, website_url: str) -> Set[str]:
        """Extract emails from business website"""
        emails = set()
        
        if not website_url:
            return emails
            
        try:
            # Clean URL
            if not website_url.startswith('http'):
                website_url = 'https://' + website_url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Pages to check
            pages_to_check = [
                '',
                '/contact',
                '/about',
                '/contact-us',
                '/about-us'
            ]
            
            for page in pages_to_check:
                try:
                    url = website_url.rstrip('/') + page
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        # Extract from HTML
                        soup = BeautifulSoup(response.content, 'html.parser')
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
                    
        except Exception as e:
            print(f"Error extracting emails from {website_url}: {e}")
            
        return emails
    
    def scrape_businesses_with_emails(self, query: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Complete pipeline: Find businesses and extract their emails"""
        print(f"Searching for '{query}' in '{location}'...")
        
        # Step 1: Get businesses from Google Maps
        businesses = self.search_google_maps(query, location, max_results)
        print(f"Found {len(businesses)} businesses")
        
        # Step 2: Extract emails from each business website
        results = []
        for i, business in enumerate(businesses):
            print(f"Processing {i+1}/{len(businesses)}: {business['name']}")
            
            emails = set()
            if business['website']:
                emails = self.extract_emails_from_website(business['website'])
            
            business['emails'] = list(emails)
            business['email_count'] = len(emails)
            
            if emails:  # Only keep businesses with emails
                results.append(business)
            
            time.sleep(1)  # Rate limiting
        
        print(f"Found emails for {len(results)} businesses")
        return results

# Usage examples for trading/finance businesses
if __name__ == "__main__":
    scraper = GoogleMapsScraper()
    
    # Search for financial advisors
    results = scraper.scrape_businesses_with_emails(
        query="financial advisor", 
        location="New York", 
        max_results=20
    )
    
    print(f"\nResults:")
    for business in results:
        print(f"\n{business['name']}")
        print(f"Website: {business['website']}")
        print(f"Emails: {', '.join(business['emails'])}")
        print(f"Phone: {business['phone']}")
        print(f"Address: {business['address']}")