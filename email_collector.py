import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import asyncio
import aiohttp
from typing import List, Dict, Set
from datetime import datetime
from sqlalchemy.orm import Session
from models import Email, EmailList
import os
import json

class EmailCollector:
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
    def extract_emails_from_text(self, text: str) -> Set[str]:
        """Extract email addresses from text"""
        return set(self.email_pattern.findall(text))
    
    def scrape_website(self, url: str) -> Set[str]:
        """Scrape emails from a website"""
        emails = set()
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            emails.update(self.extract_emails_from_text(text))
            
            # Also check href attributes
            for link in soup.find_all('a', href=True):
                if 'mailto:' in link['href']:
                    email = link['href'].replace('mailto:', '').split('?')[0]
                    if self.email_pattern.match(email):
                        emails.add(email)
                        
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
        
        return emails
    
    def scrape_with_selenium(self, url: str) -> Set[str]:
        """Scrape emails using Selenium for JavaScript-heavy sites"""
        emails = set()
        driver = None
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(url)
            driver.implicitly_wait(10)
            
            # Get page source after JavaScript execution
            page_source = driver.page_source
            emails.update(self.extract_emails_from_text(page_source))
            
        except Exception as e:
            print(f"Error with Selenium scraping {url}: {str(e)}")
        finally:
            if driver:
                driver.quit()
        
        return emails
    
    def search_google_for_emails(self, query: str, num_results: int = 50) -> Set[str]:
        """Search Google for emails (be careful with rate limits)"""
        emails = set()
        try:
            # Use Google Custom Search API or scrape search results
            search_url = f"https://www.google.com/search?q={query}+email"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract URLs from search results
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/url?q=' in href:
                    url = href.split('/url?q=')[1].split('&')[0]
                    if url.startswith('http'):
                        links.append(url)
            
            # Scrape each result page
            for url in links[:num_results]:
                try:
                    page_emails = self.scrape_website(url)
                    emails.update(page_emails)
                    import time
                    time.sleep(1)  # Be respectful
                except:
                    continue
                    
        except Exception as e:
            print(f"Error searching Google: {str(e)}")
        
        return emails
    
    def collect_from_csv(self, file_path: str) -> List[Dict]:
        """Collect emails from CSV file"""
        emails_data = []
        try:
            df = pd.read_csv(file_path)
            
            # Try to identify email column
            email_columns = [col for col in df.columns if 'email' in col.lower()]
            if not email_columns:
                # Look for columns with email-like data
                for col in df.columns:
                    if df[col].astype(str).str.contains('@').any():
                        email_columns.append(col)
            
            if email_columns:
                email_col = email_columns[0]
                for _, row in df.iterrows():
                    email = str(row[email_col]).strip()
                    if self.email_pattern.match(email):
                        email_data = {
                            'email_address': email,
                            'first_name': row.get('first_name', row.get('firstname', '')),
                            'last_name': row.get('last_name', row.get('lastname', '')),
                            'company': row.get('company', row.get('organization', '')),
                            'source': f'csv:{os.path.basename(file_path)}'
                        }
                        emails_data.append(email_data)
                        
        except Exception as e:
            print(f"Error reading CSV {file_path}: {str(e)}")
        
        return emails_data
    
    def collect_from_linkedin_sales_navigator(self, search_params: Dict) -> List[Dict]:
        """Collect emails from LinkedIn Sales Navigator (requires API access)"""
        # This would require LinkedIn API access or web scraping
        # For demo purposes, returning empty list
        print("LinkedIn Sales Navigator collection requires API setup")
        return []
    
    def collect_from_hunter_io(self, domain: str, api_key: str) -> List[Dict]:
        """Collect emails using Hunter.io API"""
        emails_data = []
        try:
            url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={api_key}"
            response = requests.get(url)
            data = response.json()
            
            if 'data' in data and 'emails' in data['data']:
                for email_info in data['data']['emails']:
                    email_data = {
                        'email_address': email_info['value'],
                        'first_name': email_info.get('first_name', ''),
                        'last_name': email_info.get('last_name', ''),
                        'company': data['data'].get('organization', ''),
                        'source': f'hunter.io:{domain}'
                    }
                    emails_data.append(email_data)
                    
        except Exception as e:
            print(f"Error with Hunter.io API: {str(e)}")
        
        return emails_data
    
    def collect_from_apollo_io(self, search_params: Dict, api_key: str) -> List[Dict]:
        """Collect emails using Apollo.io API"""
        emails_data = []
        try:
            url = "https://api.apollo.io/v1/mixed_people/search"
            headers = {
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
                'X-Api-Key': api_key
            }
            
            response = requests.post(url, headers=headers, json=search_params)
            data = response.json()
            
            if 'people' in data:
                for person in data['people']:
                    if person.get('email'):
                        email_data = {
                            'email_address': person['email'],
                            'first_name': person.get('first_name', ''),
                            'last_name': person.get('last_name', ''),
                            'company': person.get('organization', {}).get('name', ''),
                            'industry': person.get('organization', {}).get('industry', ''),
                            'source': 'apollo.io'
                        }
                        emails_data.append(email_data)
                        
        except Exception as e:
            print(f"Error with Apollo.io API: {str(e)}")
        
        return emails_data
    
    async def collect_bulk_emails(self, sources: List[str], keywords: List[str], max_emails: int, db: Session):
        """Collect emails from multiple sources"""
        all_emails = []
        collected_count = 0
        
        # Create email list
        email_list = EmailList(
            name=f"Bulk Collection {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=f"Collected from: {', '.join(sources)}"
        )
        db.add(email_list)
        db.commit()
        
        for source in sources:
            if collected_count >= max_emails:
                break
                
            try:
                if source.startswith('http'):
                    # Website scraping
                    emails = self.scrape_website(source)
                    for email in emails:
                        if collected_count >= max_emails:
                            break
                        email_data = {
                            'email_address': email,
                            'source': f'website:{source}'
                        }
                        all_emails.append(email_data)
                        collected_count += 1
                
                elif source.endswith('.csv'):
                    # CSV file
                    csv_emails = self.collect_from_csv(source)
                    for email_data in csv_emails:
                        if collected_count >= max_emails:
                            break
                        all_emails.append(email_data)
                        collected_count += 1
                
                elif source.startswith('hunter:'):
                    # Hunter.io
                    domain = source.split(':')[1]
                    api_key = os.getenv('HUNTER_API_KEY')
                    if api_key:
                        hunter_emails = self.collect_from_hunter_io(domain, api_key)
                        for email_data in hunter_emails:
                            if collected_count >= max_emails:
                                break
                            all_emails.append(email_data)
                            collected_count += 1
                
                elif source.startswith('apollo:'):
                    # Apollo.io
                    api_key = os.getenv('APOLLO_API_KEY')
                    if api_key:
                        search_params = {
                            'q_keywords': ' '.join(keywords),
                            'page': 1,
                            'per_page': min(100, max_emails - collected_count)
                        }
                        apollo_emails = self.collect_from_apollo_io(search_params, api_key)
                        for email_data in apollo_emails:
                            if collected_count >= max_emails:
                                break
                            all_emails.append(email_data)
                            collected_count += 1
                            
            except Exception as e:
                print(f"Error collecting from {source}: {str(e)}")
                continue
        
        # Save emails to database
        for email_data in all_emails:
            try:
                # Check if email already exists
                existing_email = db.query(Email).filter(
                    Email.email_address == email_data['email_address']
                ).first()
                
                if not existing_email:
                    email_obj = Email(**email_data)
                    db.add(email_obj)
            except Exception as e:
                print(f"Error saving email {email_data.get('email_address')}: {str(e)}")
                continue
        
        # Update email list stats
        email_list.total_emails = collected_count
        db.commit()
        
        print(f"Collected {collected_count} emails from {len(sources)} sources")