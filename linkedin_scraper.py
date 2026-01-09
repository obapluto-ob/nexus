from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re
from typing import List, Dict

class LinkedInScraper:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    def scrape_linkedin_company(self, company_name: str) -> List[Dict]:
        """Scrape LinkedIn company page for employee info"""
        profiles = []
        driver = None
        
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            
            # Search for company
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={company_name}"
            driver.get(search_url)
            time.sleep(3)
            
            # Get profile links
            profile_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
            
            for link in profile_links[:20]:  # Limit to avoid rate limits
                try:
                    profile_url = link.get_attribute('href')
                    driver.get(profile_url)
                    time.sleep(2)
                    
                    # Extract name and title
                    name_elem = driver.find_element(By.CSS_SELECTOR, "h1")
                    title_elem = driver.find_element(By.CSS_SELECTOR, ".text-body-medium")
                    
                    profile_data = {
                        'name': name_elem.text if name_elem else '',
                        'title': title_elem.text if title_elem else '',
                        'company': company_name,
                        'profile_url': profile_url
                    }
                    profiles.append(profile_data)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"LinkedIn scraping error: {e}")
        finally:
            if driver:
                driver.quit()
                
        return profiles
    
    def scrape_google_for_linkedin_profiles(self, company: str, job_titles: List[str]) -> List[Dict]:
        """Use Google to find LinkedIn profiles"""
        profiles = []
        
        for title in job_titles:
            try:
                query = f'site:linkedin.com/in "{company}" "{title}"'
                search_url = f"https://www.google.com/search?q={query}"
                
                # This would extract LinkedIn profile URLs from Google results
                # Then scrape each profile for contact info
                
            except Exception as e:
                continue
                
        return profiles