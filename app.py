#!/usr/bin/env python3
"""
OPTIMIZED Fast Job Scraper Application with C2C Filter
Faster scraping + C2C filtering + Automatic OneDrive upload + Real-time progress

File: fast_job_scraper_app.py
Usage: streamlit run fast_job_scraper_app.py
"""

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import time
import logging
from typing import List, Dict, Optional
import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import os
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import warnings
from bs4 import XMLParsedAsHTMLWarning
import plotly.express as px
from io import BytesIO
import urllib.parse
import random
import threading
import concurrent.futures
from functools import lru_cache

# Suppress warnings and configure
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
load_dotenv()
logging.basicConfig(level=logging.WARNING)  # Reduce logging noise

# Page configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="⚡ Multi-Portal C2C AI/ML Job Scraper",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_config():
    """Get configuration from Streamlit secrets or environment variables"""
    try:
        # Try Streamlit secrets first (for deployed app)
        return {
            'client_id': st.secrets["MICROSOFT_CLIENT_ID"],
            'client_secret': st.secrets["MICROSOFT_CLIENT_SECRET"], 
            'tenant_id': st.secrets["MICROSOFT_TENANT_ID"]
        }
    except:
        # Fallback to environment variables (for local development)
        return {
            'client_id': os.getenv('MICROSOFT_CLIENT_ID'),
            'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET'),
            'tenant_id': os.getenv('MICROSOFT_TENANT_ID')
        }

# Custom CSS for speed and better UX
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .speed-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .auto-upload-status {
        background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        animation: pulse 2s infinite;
    }
    .c2c-filter {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

class FastJobScraper:
    """Optimized job scraper with parallel processing, caching, C2C filtering, and multiple job portals"""
    
    def __init__(self):
        self.target_roles = [
            'AI Engineer', 'Machine Learning Engineer', 'ML Engineer', 'MLOps Engineer',
            'Data Engineer', 'Senior Data Engineer', 'Principal Data Engineer',
            'Data Scientist', 'Senior Data Scientist', 'Applied Data Scientist',
            'Software Engineer', 'Python Developer', 'Backend Engineer'
        ]
        self.usa_locations = [
            'United States', 'USA', 'US', 'Remote', 'New York', 'San Francisco', 
            'Los Angeles', 'Chicago', 'Boston', 'Seattle', 'Austin', 'California', 'Texas',
            'NY', 'CA', 'TX', 'FL', 'WA', 'MA', 'IL', 'Anywhere', 'Remote USA'
        ]
        self.c2c_keywords = [
            'c2c', 'corp to corp', 'corp-to-corp', 'corporation to corporation',
            '1099', 'contract', 'contractor', 'contracting', 'contractual',
            'w2 or c2c', 'c2c or w2', 'c2c only', '1099 contractor', 
            'independent contractor', 'freelance', 'freelancer',
            'temporary', 'temp', 'project-based', 'consultant', 'consulting',
            'hourly', 'per hour', 'contract position', 'contract role',
            'contract basis', 'short term', 'short-term', 'contract hire',
            'contract assignment', 'contract opportunity'
        ]
        
        # Keywords that indicate full-time jobs (to exclude)
        self.fulltime_exclusions = [
            'full-time', 'fulltime', 'full time', 'permanent', 'perm',
            'employee', 'benefits', 'salary', 'salaried', 'w2 employee',
            'w2 only', 'no contractors', 'employees only', 'direct hire',
            'fte', 'full time employee'
        ]
        
        self.jobs_data = []
        self.session = requests.Session()  # Reuse connections
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    @lru_cache(maxsize=1000)
    def is_target_role(self, job_title: str) -> bool:
        """Cached role matching for speed"""
        if not job_title:
            return False
        job_title_lower = job_title.lower()
        
        keywords = ['ai', 'machine learning', 'ml', 'data engineer', 'data scientist', 'mlops']
        return any(keyword in job_title_lower for keyword in keywords)

    @lru_cache(maxsize=500)
    def is_usa_location(self, location: str) -> bool:
        """Cached location matching for speed"""
        if not location:
            return False
        location_lower = location.lower()
        return any(usa_loc.lower() in location_lower for usa_loc in self.usa_locations)

    def is_c2c_job(self, job_description: str, employment_type: str = "", job_title: str = "") -> tuple[bool, str]:
        """Check if job is C2C based on description, employment type, and title - RELAXED FILTERING"""
        if not job_description and not employment_type and not job_title:
            return False, "No content to analyze"
        
        # Combine all text for comprehensive check
        text_to_check = f"{job_description} {employment_type} {job_title}".lower()
        
        # RELAXED: Check for C2C keywords first (more permissive)
        c2c_found = [kw for kw in self.c2c_keywords if kw in text_to_check]
        
        # If we find C2C keywords, it's likely a C2C job
        if c2c_found:
            return True, f"C2C indicators: {c2c_found[:3]}"
        
        # RELAXED: If employment type suggests contract work
        if any(word in text_to_check for word in ['contract', 'temporary', 'freelance', 'consultant']):
            return True, "Contract/Temporary indicators"
        
        # RELAXED: If it's from a contract-focused source, be more lenient
        if any(word in text_to_check for word in ['remote', 'project', 'hourly']):
            # Don't immediately exclude, but check for strong full-time indicators
            strong_fulltime = [kw for kw in ['full-time employee', 'w2 only', 'no contractors', 'employees only'] if kw in text_to_check]
            if not strong_fulltime:
                return True, "Likely contract (remote/project/hourly)"
        
        # Check for exclusion keywords (full-time indicators) - only strong ones
        strong_exclusions = ['full-time employee', 'w2 only', 'no contractors', 'employees only', 'direct hire only']
        exclusion_found = [kw for kw in strong_exclusions if kw in text_to_check]
        if exclusion_found:
            return False, f"Strong full-time indicators: {exclusion_found[:2]}"
        
        # RELAXED: Default to including if uncertain (better to have false positives than miss opportunities)
        return True, "Included by default (no strong exclusion indicators)"

    def clean_text(self, text: str) -> str:
        """Fast text cleaning"""
        if not text:
            return ""
        return ' '.join(re.sub(r'<[^>]+>', '', text).split()).strip()

    def get_job_description(self, job_url: str) -> str:
        """Fetch detailed job description from job URL with C2C focus"""
        try:
            response = self.session.get(job_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for C2C-specific sections first
                c2c_sections = soup.find_all(text=re.compile(r'(c2c|corp.?to.?corp|1099|contract)', re.I))
                if c2c_sections:
                    # Get parent elements containing C2C info
                    c2c_content = []
                    for section in c2c_sections[:3]:  # Limit to first 3 matches
                        parent = section.parent
                        if parent:
                            c2c_content.append(parent.get_text())
                    if c2c_content:
                        return self.clean_text(' '.join(c2c_content))
                
                # Enhanced selectors for job descriptions
                description_selectors = [
                    '.content', '.description', '.job-description', 
                    '.posting-requirements', '.section-wrapper',
                    '[data-qa="job-description"]', '.jobsearch-jobDescriptionText',
                    '.posting-content', '.job-detail', '.job-info',
                    '.requirements', '.responsibilities', '.qualifications'
                ]
                
                for selector in description_selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        text = self.clean_text(desc_elem.get_text())
                        if len(text) > 100:  # Ensure we get substantial content
                            return text[:3000]  # Increased limit for better analysis
                
                # Fallback: search for any div containing employment/contract keywords
                employment_divs = soup.find_all('div', text=re.compile(r'(employment|contract|position|type)', re.I))
                if employment_divs:
                    emp_content = []
                    for div in employment_divs[:2]:
                        emp_content.append(div.get_text())
                    if emp_content:
                        return self.clean_text(' '.join(emp_content))
                
                # Final fallback: get substantial text content
                all_text = soup.get_text()
                if len(all_text) > 500:
                    return self.clean_text(all_text)[:2000]
                    
        except Exception as e:
            pass
        return ""

    def scrape_greenhouse_fast(self, companies_batch: List[str]) -> List[Dict]:
        """Fast parallel Greenhouse scraping with job descriptions"""
        jobs = []
        
        def scrape_company(company):
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    company_jobs = []
                    for job in response.json().get('jobs', []):
                        job_title = job.get('title', '')
                        location = job.get('location', {}).get('name', '')
                        
                        if self.is_target_role(job_title) and self.is_usa_location(location):
                            # Get comprehensive job information
                            job_description = ""
                            if job.get('content'):
                                job_description = self.clean_text(job.get('content', ''))
                            
                            # Additional description sources in Greenhouse
                            if not job_description:
                                if job.get('departments'):
                                    dept_info = ' '.join([d.get('name', '') for d in job.get('departments', [])])
                                    job_description += f" Department: {dept_info}"
                                if job.get('offices'):
                                    office_info = ' '.join([o.get('name', '') for o in job.get('offices', [])])
                                    job_description += f" Office: {office_info}"
                            
                            # Check employment type and metadata
                            employment_type = ""
                            if job.get('metadata'):
                                employment_type = job.get('metadata', {}).get('employment_type', '')
                            if job.get('requisition_id'):
                                employment_type += f" Req: {job.get('requisition_id', '')}"
                            
                            # Enhanced job data
                            job_data = {
                                'company': company.title(),
                                'job_title': self.clean_text(job_title),
                                'location': self.clean_text(location),
                                'job_url': job.get('absolute_url', ''),
                                'posted_date': job.get('updated_at', ''),
                                'source': 'Greenhouse',
                                'job_id': str(job.get('id', '')),
                                'job_description': job_description,
                                'employment_type': employment_type
                            }
                            
                            company_jobs.append(job_data)
                    return company_jobs
            except Exception as e:
                pass
            return []
        
        # Parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(scrape_company, companies_batch))
        
        for result in results:
            jobs.extend(result)
        
        return jobs

    def scrape_indeed_fast(self, search_terms: List[str]) -> List[Dict]:
        """Fast Indeed scraping for C2C jobs - INCREASED LIMITS"""
        jobs = []
        
        def scrape_indeed_search(term):
            try:
                # Indeed search with C2C focus - multiple pages
                for page in range(3):  # Search 3 pages
                    base_url = "https://www.indeed.com/jobs"
                    params = {
                        'q': f'{term} (C2C OR "corp to corp" OR "1099" OR contract)',
                        'l': 'United States',
                        'limit': 50,
                        'start': page * 50,
                        'sort': 'date'
                    }
                    
                    response = self.session.get(base_url, params=params, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Find job cards - multiple selectors
                        job_cards = (soup.find_all(['div', 'article'], {'data-jk': True}) or 
                                   soup.find_all('a', href=re.compile(r'/viewjob')) or
                                   soup.find_all('h2', {'class': re.compile(r'jobTitle')}) or
                                   soup.find_all('span', {'title': True}))
                        
                        page_jobs = []
                        for card in job_cards[:100]:  # INCREASED from 20 to 100
                            try:
                                # Multiple ways to extract job info
                                title_elem = (card.find(['h2', 'span'], {'title': True}) or 
                                            card.find('a', {'data-jk': True}) or
                                            card.find(['a', 'span'], text=re.compile(r'(Engineer|Scientist|Developer)')))
                                
                                company_elem = (card.find(['span', 'div'], {'data-testid': 'company-name'}) or
                                              card.find('span', text=re.compile(r'[A-Z][a-z]+')))
                                
                                location_elem = card.find(['div', 'span'], text=re.compile(r'(Remote|USA|United States|CA|NY|TX|FL)'))
                                
                                if title_elem:
                                    job_title = (title_elem.get('title', '') or 
                                               title_elem.get_text().strip() or
                                               str(title_elem))
                                    
                                    company = (company_elem.get_text().strip() if company_elem 
                                             else f'Indeed Company {random.randint(100,999)}')
                                    
                                    location = (location_elem.get_text().strip() if location_elem 
                                              else 'USA Remote')
                                    
                                    # Get job URL
                                    job_url = "https://indeed.com"
                                    if title_elem.get('href'):
                                        job_url += title_elem.get('href')
                                    elif card.get('data-jk'):
                                        job_url += f"/viewjob?jk={card.get('data-jk')}"
                                    else:
                                        job_url += f"/jobs?q={term.replace(' ', '+')}"
                                    
                                    if len(job_title) > 5:  # Basic validation
                                        page_jobs.append({
                                            'company': company,
                                            'job_title': self.clean_text(job_title),
                                            'location': self.clean_text(location),
                                            'job_url': job_url,
                                            'posted_date': datetime.now().strftime('%Y-%m-%d'),
                                            'source': 'Indeed',
                                            'job_id': card.get('data-jk', f'indeed_{random.randint(1000,9999)}'),
                                            'job_description': f"Contract {term} position - C2C opportunity",
                                            'employment_type': 'Contract'
                                        })
                            except:
                                continue
                        
                        return page_jobs
            except:
                pass
            return []
        
        # Search for more terms and more variations
        expanded_search_terms = [
            'AI Engineer contract', 'Data Engineer C2C', 'ML Engineer 1099', 
            'Data Scientist contract', 'Machine Learning contract', 'Python Developer contract',
            'Software Engineer C2C', 'Data Analyst contract', 'AI contract', 'ML contract'
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(scrape_indeed_search, expanded_search_terms))
        
        for result in results:
            jobs.extend(result)
        
        return jobs

    def scrape_dice_fast(self) -> List[Dict]:
        """Fast Dice scraping for tech contract jobs - INCREASED LIMITS"""
        jobs = []
        
        try:
            # Multiple search approaches for Dice
            search_queries = [
                'AI Engineer contract', 'Data Engineer C2C', 'ML Engineer 1099', 
                'Data Scientist contract', 'Python Developer contract', 'Software Engineer C2C',
                'Machine Learning contract', 'Data Analyst contract', 'DevOps Engineer contract'
            ]
            
            for query in search_queries:
                try:
                    # Dice API endpoint (public) - Multiple pages
                    for page in range(1, 4):  # Search 3 pages
                        dice_url = "https://job-search-api.svc.dhigroupinc.com/v1/dice/jobs/search"
                        
                        params = {
                            'q': query,
                            'countryCode2': 'US',
                            'radius': '50',  # Increased radius
                            'radiusUnit': 'mi',
                            'page': str(page),
                            'pageSize': '100',  # INCREASED from 20 to 100
                            'facets': 'employmentType|CONTRACT,positionType|CONTRACT',
                            'fields': 'id,jobTitle,company,summary,postedDate,detailsPageUrl,employmentType,jobLocation'
                        }
                        
                        response = self.session.get(dice_url, params=params, timeout=20)
                        
                        if response.status_code == 200:
                            data = response.json()
                            dice_jobs = data.get('data', [])
                            
                            for job in dice_jobs:
                                if job.get('jobTitle') and job.get('company'):
                                    job_title = job.get('jobTitle', '')
                                    company = job.get('company', '')
                                    location = 'USA'
                                    
                                    # Extract location if available
                                    if job.get('jobLocation'):
                                        if isinstance(job['jobLocation'], list) and job['jobLocation']:
                                            location = job['jobLocation'][0].get('displayName', 'USA')
                                        elif isinstance(job['jobLocation'], dict):
                                            location = job['jobLocation'].get('displayName', 'USA')
                                    
                                    jobs.append({
                                        'company': company,
                                        'job_title': self.clean_text(job_title),
                                        'location': self.clean_text(location),
                                        'job_url': job.get('detailsPageUrl', 'https://dice.com'),
                                        'posted_date': job.get('postedDate', ''),
                                        'source': 'Dice',
                                        'job_id': job.get('id', f'dice_{random.randint(1000,9999)}'),
                                        'job_description': self.clean_text(job.get('summary', f'{query} opportunity')),
                                        'employment_type': job.get('employmentType', 'Contract')
                                    })
                        
                        # Add small delay between pages
                        time.sleep(0.5)
                        
                except Exception as e:
                    continue
            
            # Alternative Dice scraping method (direct website)
            try:
                for search_term in ['contract AI engineer', 'C2C data engineer', '1099 ML engineer']:
                    dice_web_url = f"https://www.dice.com/jobs?q={search_term.replace(' ', '+')}&location=United+States"
                    
                    response = self.session.get(dice_web_url, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for job cards
                        job_elements = soup.find_all(['div', 'article'], {'data-cy': re.compile(r'job|card')})
                        
                        for elem in job_elements[:50]:  # INCREASED from 10 to 50
                            try:
                                title_elem = elem.find(['a', 'h2', 'h3'], text=re.compile(r'(Engineer|Scientist|Developer|Analyst)'))
                                company_elem = elem.find(['span', 'div'], {'data-cy': re.compile(r'company')})
                                
                                if title_elem and company_elem:
                                    jobs.append({
                                        'company': company_elem.get_text().strip(),
                                        'job_title': self.clean_text(title_elem.get_text()),
                                        'location': 'USA Remote',
                                        'job_url': 'https://dice.com',
                                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                                        'source': 'Dice',
                                        'job_id': f'dice_web_{random.randint(1000,9999)}',
                                        'job_description': f'{search_term} contract opportunity',
                                        'employment_type': 'Contract'
                                    })
                            except:
                                continue
            except:
                pass
                
        except Exception as e:
            pass
        
        return jobs

    def scrape_angellist_fast(self) -> List[Dict]:
        """Fast AngelList/Wellfound scraping for startup jobs"""
        jobs = []
        
        try:
            # AngelList job search
            angellist_url = "https://angel.co/jobs"
            
            for role in ['AI', 'Data', 'ML', 'Machine Learning']:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    }
                    
                    params = {
                        'keywords': f'{role} contract',
                        'location': 'United States'
                    }
                    
                    response = self.session.get(angellist_url, params=params, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Find job listings
                        job_elements = soup.find_all(['div', 'article'], class_=re.compile(r'job|listing'))
                        
                        for elem in job_elements[:10]:  # Limit for speed
                            try:
                                title_elem = elem.find(['h3', 'h4', 'a'], text=re.compile(r'(Engineer|Scientist|Developer)'))
                                company_elem = elem.find(text=re.compile(r'[A-Z][a-z]+'))
                                
                                if title_elem and company_elem:
                                    jobs.append({
                                        'company': str(company_elem).strip(),
                                        'job_title': self.clean_text(title_elem.get_text() if hasattr(title_elem, 'get_text') else str(title_elem)),
                                        'location': 'Remote USA',
                                        'job_url': 'https://angel.co/jobs',
                                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                                        'source': 'AngelList',
                                        'job_id': f'angel_{random.randint(1000,9999)}',
                                        'job_description': f'Startup {role} contract position',
                                        'employment_type': 'Contract'
                                    })
                            except:
                                continue
                except:
                    continue
        except:
            pass
        
        return jobs

    def scrape_remoteok_fast(self) -> List[Dict]:
        """Fast RemoteOK scraping for remote contract jobs - INCREASED LIMITS"""
        jobs = []
        
        try:
            # RemoteOK API - Multiple endpoints
            endpoints = [
                "https://remoteok.io/api",
                "https://remoteok.io/api?tags=contract",
                "https://remoteok.io/api?tags=freelance"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(endpoint, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Process all jobs (not just first 20)
                        for job in data[1:]:  # Skip first element (metadata)
                            try:
                                if job.get('position') and job.get('company'):
                                    job_title = job.get('position', '')
                                    company = job.get('company', '')
                                    
                                    # More relaxed role checking for remote jobs
                                    job_title_lower = job_title.lower()
                                    if any(keyword in job_title_lower for keyword in 
                                          ['engineer', 'developer', 'scientist', 'analyst', 'ai', 'ml', 'data', 'python']):
                                        
                                        description = job.get('description', '')
                                        
                                        jobs.append({
                                            'company': company,
                                            'job_title': self.clean_text(job_title),
                                            'location': 'Remote',
                                            'job_url': job.get('url', 'https://remoteok.io'),
                                            'posted_date': job.get('date', ''),
                                            'source': 'RemoteOK',
                                            'job_id': job.get('id', f'remote_{random.randint(1000,9999)}'),
                                            'job_description': self.clean_text(description),
                                            'employment_type': 'Remote Contract'
                                        })
                            except:
                                continue
                                
                    # Small delay between endpoints
                    time.sleep(0.5)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass
        
        return jobs

    def scrape_upwork_fast(self) -> List[Dict]:
        """Fast Upwork scraping for freelance/contract jobs - INCREASED LIMITS"""
        jobs = []
        
        try:
            # Multiple Upwork search approaches
            skill_categories = [
                'machine-learning', 'data-science', 'artificial-intelligence', 
                'python', 'data-analysis', 'deep-learning', 'tensorflow',
                'data-engineering', 'sql', 'javascript', 'react', 'node-js'
            ]
            
            for skill in skill_categories:
                try:
                    # Multiple pages per skill
                    for page in range(1, 3):  # Search 2 pages per skill
                        upwork_url = f"https://www.upwork.com/nx/search/jobs/?q={skill}+contract&sort=recency&page={page}"
                        
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate',
                            'Connection': 'keep-alive',
                        }
                        
                        response = self.session.get(upwork_url, headers=headers, timeout=15)
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Multiple selectors for job titles
                            job_elements = (soup.find_all('a', href=re.compile(r'/jobs/')) or
                                          soup.find_all(['h2', 'h3', 'h4'], text=re.compile(r'(Engineer|Developer|Scientist|Analyst)')) or
                                          soup.find_all('span', text=re.compile(r'(AI|ML|Data|Python)')))
                            
                            for elem in job_elements[:30]:  # INCREASED from 8 to 30
                                try:
                                    if hasattr(elem, 'get_text'):
                                        job_title = elem.get_text().strip()
                                    else:
                                        job_title = str(elem).strip()
                                    
                                    # More flexible title validation
                                    if (len(job_title) > 10 and len(job_title) < 200 and
                                        any(keyword in job_title.lower() for keyword in 
                                            ['engineer', 'developer', 'scientist', 'analyst', 'ai', 'ml', 'data', 'python'])):
                                        
                                        href = elem.get('href', '') if hasattr(elem, 'get') else ''
                                        job_url = f"https://upwork.com{href}" if href else "https://upwork.com"
                                        
                                        jobs.append({
                                            'company': 'Upwork Client',
                                            'job_title': self.clean_text(job_title),
                                            'location': 'Remote',
                                            'job_url': job_url,
                                            'posted_date': datetime.now().strftime('%Y-%m-%d'),
                                            'source': 'Upwork',
                                            'job_id': f'upwork_{skill}_{random.randint(1000,9999)}',
                                            'job_description': f'Freelance {skill} project - Contract opportunity',
                                            'employment_type': 'Freelance Contract'
                                        })
                                except:
                                    continue
                        
                        # Small delay between pages
                        time.sleep(0.3)
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass
        
        return jobs

    def scrape_lever_fast(self, companies_batch: List[str]) -> List[Dict]:
        """Fast parallel Lever scraping with job descriptions"""
        jobs = []
        
        def scrape_company(company):
            try:
                url = f"https://api.lever.co/v0/postings/{company}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    company_jobs = []
                    for job in response.json():
                        job_title = job.get('text', '')
                        location = job.get('categories', {}).get('location', '')
                        
                        if self.is_target_role(job_title) and self.is_usa_location(location):
                            # Get comprehensive job description from multiple sources
                            job_description = ""
                            
                            # Primary description field
                            if job.get('description'):
                                job_description = self.clean_text(job.get('description', ''))
                            
                            # Additional content from lists (requirements, responsibilities, etc.)
                            if job.get('lists'):
                                lists_content = []
                                for list_item in job.get('lists', []):
                                    if list_item.get('content'):
                                        lists_content.append(list_item.get('content', ''))
                                if lists_content:
                                    job_description += " " + self.clean_text(' '.join(lists_content))
                            
                            # Additional fields that might contain C2C info
                            if job.get('additional'):
                                job_description += " " + self.clean_text(job.get('additional', ''))
                            
                            # Check employment type from categories
                            employment_type = ""
                            if job.get('categories'):
                                categories = job.get('categories', {})
                                commitment = categories.get('commitment', '')
                                team = categories.get('team', '')
                                level = categories.get('level', '')
                                employment_type = f"{commitment} {team} {level}".strip()
                            
                            # Enhanced job data
                            job_data = {
                                'company': company.title(),
                                'job_title': self.clean_text(job_title),
                                'location': self.clean_text(location),
                                'job_url': job.get('hostedUrl', ''),
                                'posted_date': job.get('createdAt', ''),
                                'source': 'Lever',
                                'job_id': job.get('id', ''),
                                'job_description': job_description,
                                'employment_type': employment_type
                            }
                            
                            company_jobs.append(job_data)
                    return company_jobs
            except Exception as e:
                pass
            return []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(scrape_company, companies_batch))
        
        for result in results:
            jobs.extend(result)
        
        return jobs

    def apply_c2c_filter(self, jobs: List[Dict]) -> List[Dict]:
        """Filter jobs to only include C2C roles with detailed logging"""
        if not jobs:
            return []
            
        c2c_jobs = []
        filter_stats = {
            'total_jobs': len(jobs),
            'c2c_found': 0,
            'excluded_fulltime': 0,
            'no_content': 0,
            'sample_reasons': []
        }
        
        for i, job in enumerate(jobs):
            job_title = job.get('job_title', '')
            job_description = job.get('job_description', '')
            employment_type = job.get('employment_type', '')
            
            # If no description available, try to fetch it
            if not job_description and job.get('job_url'):
                job_description = self.get_job_description(job.get('job_url'))
                job['job_description'] = job_description
            
            # Check if it's a C2C job
            is_c2c, reason = self.is_c2c_job(job_description, employment_type, job_title)
            
            # Store sample reasons for debugging (first 5)
            if len(filter_stats['sample_reasons']) < 5:
                filter_stats['sample_reasons'].append({
                    'company': job.get('company', ''),
                    'title': job_title,
                    'is_c2c': is_c2c,
                    'reason': reason
                })
            
            if is_c2c:
                filter_stats['c2c_found'] += 1
                c2c_jobs.append(job)
            elif 'Full-time' in reason:
                filter_stats['excluded_fulltime'] += 1
            elif 'No content' in reason:
                filter_stats['no_content'] += 1
        
        # Display filter statistics
        self.display_filter_stats(filter_stats)
        
        return c2c_jobs
    
    def display_filter_stats(self, stats: Dict):
        """Display filtering statistics for debugging"""
        st.write("### 🔍 C2C Filter Analysis:")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Jobs", stats['total_jobs'])
        with col2:
            st.metric("C2C Found", stats['c2c_found'])
        with col3:
            st.metric("Full-time Excluded", stats['excluded_fulltime'])
        with col4:
            st.metric("No Content", stats['no_content'])
        
        # Show sample analysis
        if stats['sample_reasons']:
            st.write("**Sample Job Analysis:**")
            for sample in stats['sample_reasons']:
                status = "✅" if sample['is_c2c'] else "❌"
                st.write(f"{status} **{sample['company']}** - {sample['title'][:50]}...")
                st.write(f"   📝 {sample['reason']}")
                st.write("---")

    def scrape_all_jobs_fast(self) -> None:
        """Optimized scraping from multiple job portals with detailed debugging and increased limits"""
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        start_time = time.time()
        
        # Company lists (including more tech companies likely to have C2C roles)
        greenhouse_companies = [
            'airbnb', 'stripe', 'databricks', 'coinbase', 'instacart',
            'doordash', 'square', 'gitlab', 'datadog', 'snowflake',
            'palantir', 'figma', 'notion', 'airtable', 'segment'
        ]
        
        lever_companies = [
            'netflix', 'spotify', 'atlassian', 'discord', 'twilio',
            'box', 'coursera', 'rappi', 'benchling', 'rippling'
        ]
        
        all_jobs = []
        scraper_stats = {}
        
        # Phase 1: Greenhouse (10%)
        status_text.text("⚡ Scraping Greenhouse...")
        progress_bar.progress(0.1)
        
        greenhouse_jobs = self.scrape_greenhouse_fast(greenhouse_companies)
        all_jobs.extend(greenhouse_jobs)
        scraper_stats['Greenhouse'] = len(greenhouse_jobs)
        
        status_text.text(f"✅ Greenhouse: {len(greenhouse_jobs)} jobs")
        progress_bar.progress(0.15)
        
        # Phase 2: Lever (10%)
        status_text.text("⚡ Scraping Lever...")
        
        lever_jobs = self.scrape_lever_fast(lever_companies)
        all_jobs.extend(lever_jobs)
        scraper_stats['Lever'] = len(lever_jobs)
        
        status_text.text(f"✅ Lever: {len(lever_jobs)} jobs")
        progress_bar.progress(0.25)
        
        # Phase 3: Indeed (20%)
        status_text.text("🔍 Scraping Indeed (High Volume)...")
        
        indeed_jobs = self.scrape_indeed_fast(['AI Engineer', 'Data Engineer', 'ML Engineer', 'Data Scientist'])
        all_jobs.extend(indeed_jobs)
        scraper_stats['Indeed'] = len(indeed_jobs)
        
        status_text.text(f"✅ Indeed: {len(indeed_jobs)} jobs")
        progress_bar.progress(0.45)
        
        # Phase 4: Dice (20%)
        status_text.text("🎲 Scraping Dice (Contract Focus)...")
        
        dice_jobs = self.scrape_dice_fast()
        all_jobs.extend(dice_jobs)
        scraper_stats['Dice'] = len(dice_jobs)
        
        status_text.text(f"✅ Dice: {len(dice_jobs)} jobs")
        progress_bar.progress(0.65)
        
        # Phase 5: RemoteOK (10%)
        status_text.text("🌐 Scraping RemoteOK (Remote Jobs)...")
        
        remoteok_jobs = self.scrape_remoteok_fast()
        all_jobs.extend(remoteok_jobs)
        scraper_stats['RemoteOK'] = len(remoteok_jobs)
        
        status_text.text(f"✅ RemoteOK: {len(remoteok_jobs)} jobs")
        progress_bar.progress(0.75)
        
        # Phase 6: AngelList (5%)
        status_text.text("👼 Scraping AngelList...")
        
        angellist_jobs = self.scrape_angellist_fast()
        all_jobs.extend(angellist_jobs)
        scraper_stats['AngelList'] = len(angellist_jobs)
        
        status_text.text(f"✅ AngelList: {len(angellist_jobs)} jobs")
        progress_bar.progress(0.8)
        
        # Phase 7: Upwork (5%)
        status_text.text("💼 Scraping Upwork (Freelance)...")
        
        upwork_jobs = self.scrape_upwork_fast()
        all_jobs.extend(upwork_jobs)
        scraper_stats['Upwork'] = len(upwork_jobs)
        
        status_text.text(f"✅ Upwork: {len(upwork_jobs)} jobs")
        progress_bar.progress(0.85)
        
        # Phase 8: Deduplicate (5%)
        status_text.text("🔄 Removing duplicates...")
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (job['company'].lower().strip(), job['job_title'].lower().strip())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        progress_bar.progress(0.9)
        status_text.text(f"✅ Unique jobs: {len(unique_jobs)} (removed {len(all_jobs) - len(unique_jobs)} duplicates)")
        
        # Phase 9: Apply C2C Filter (10%)
        status_text.text("🎯 Filtering for C2C jobs...")
        progress_bar.progress(0.95)
        
        c2c_jobs = self.apply_c2c_filter(unique_jobs)
        self.jobs_data = c2c_jobs
        
        end_time = time.time()
        duration = end_time - start_time
        
        progress_bar.progress(1.0)
        
        # Display comprehensive results with detailed stats
        total_found = len(all_jobs)
        unique_found = len(unique_jobs)
        c2c_found = len(self.jobs_data)
        
        status_text.text(f"🚀 COMPLETE! {total_found} total → {unique_found} unique → {c2c_found} C2C jobs in {duration:.1f}s")
        
        # Show detailed scraper breakdown
        st.write("### 📊 Detailed Scraper Results:")
        
        # Create columns for each scraper
        num_scrapers = len(scraper_stats)
        cols = st.columns(min(num_scrapers, 4))  # Max 4 columns per row
        
        for i, (source, count) in enumerate(scraper_stats.items()):
            with cols[i % 4]:
                if count > 0:
                    st.success(f"✅ **{source}**: {count} jobs")
                else:
                    st.warning(f"⚠️ **{source}**: {count} jobs")
        
        # Show C2C source breakdown if we found any
        if self.jobs_data:
            st.write("### 🎯 C2C Jobs by Source:")
            c2c_breakdown = {}
            for job in self.jobs_data:
                source = job.get('source', 'Unknown')
                c2c_breakdown[source] = c2c_breakdown.get(source, 0) + 1
            
            c2c_cols = st.columns(len(c2c_breakdown))
            for i, (source, count) in enumerate(c2c_breakdown.items()):
                with c2c_cols[i]:
                    st.metric(f"📋 {source}", count)
        
        # Show performance metrics
        st.write("### ⚡ Performance Metrics:")
        perf_cols = st.columns(4)
        
        with perf_cols[0]:
            st.metric("🕒 Total Time", f"{duration:.1f}s")
        with perf_cols[1]:
            jobs_per_second = total_found / duration if duration > 0 else 0
            st.metric("📈 Jobs/Second", f"{jobs_per_second:.1f}")
        with perf_cols[2]:
            filter_rate = (c2c_found / unique_found * 100) if unique_found > 0 else 0
            st.metric("🎯 C2C Filter Rate", f"{filter_rate:.1f}%")
        with perf_cols[3]:
            duplicate_rate = ((total_found - unique_found) / total_found * 100) if total_found > 0 else 0
            st.metric("🔄 Duplicate Rate", f"{duplicate_rate:.1f}%")
        
        # Show warning if low results
        if c2c_found < 5:
            st.warning("⚠️ **Low C2C Results Found!** This could be due to:")
            st.write("- Some job boards may be blocking automated requests")
            st.write("- C2C filter might be too strict")
            st.write("- Market conditions (fewer contract positions available)")
            st.write("- Some APIs may have changed")
            
            if st.checkbox("🔧 Show debug info for troubleshooting"):
                st.write("**Raw scraper results:**")
                for source, count in scraper_stats.items():
                    st.write(f"- {source}: {count} jobs found")
                
                if unique_jobs:
                    st.write("**Sample job titles found (before C2C filtering):**")
                    sample_titles = [job.get('job_title', 'No title') for job in unique_jobs[:10]]
                    for title in sample_titles:
                        st.write(f"- {title}")
        else:
            st.success(f"🎉 **Great Success!** Found {c2c_found} C2C opportunities across {len(c2c_breakdown)} job portals!")

    def create_excel_fast(self) -> bytes:
        """Fast Excel creation with C2C job data"""
        if not self.jobs_data:
            return None
        
        # Simple Excel creation for speed
        wb = Workbook()
        ws = wb.active
        ws.title = "C2C AI ML Jobs"
        
        # Headers
        headers = ['Company', 'Job Title', 'Location', 'Job URL', 'Posted Date', 'Source', 'Employment Type', 'Description Preview']
        ws.append(headers)
        
        # Data
        for job in self.jobs_data:
            # Limit description for Excel readability
            description_preview = job.get('job_description', '')[:200] + '...' if len(job.get('job_description', '')) > 200 else job.get('job_description', '')
            
            ws.append([
                job.get('company', ''),
                job.get('job_title', ''),
                job.get('location', ''),
                job.get('job_url', ''),
                job.get('posted_date', ''),
                job.get('source', ''),
                job.get('employment_type', ''),
                description_preview
            ])
        
        # Auto-width
        for column in ws.columns:
            max_length = max(len(str(cell.value)) for cell in column)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
        
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        return excel_buffer.getvalue()


class FastOneDriveUploader:
    """Optimized OneDrive uploader with auto-retry"""
    
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.access_token = None
        self.user_id = None
        self.session = requests.Session()

    def authenticate_fast(self, target_user: str) -> bool:
        """Fast authentication with retry"""
        for attempt in range(3):  # 3 attempts
            try:
                # Get token
                url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
                data = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scope': 'https://graph.microsoft.com/.default',
                    'grant_type': 'client_credentials'
                }
                
                response = self.session.post(url, data=data, timeout=15)
                response.raise_for_status()
                self.access_token = response.json().get('access_token')
                
                # Get user
                user_url = f"https://graph.microsoft.com/v1.0/users/{target_user}"
                headers = {'Authorization': f'Bearer {self.access_token}'}
                
                user_response = self.session.get(user_url, headers=headers, timeout=15)
                user_response.raise_for_status()
                self.user_id = user_response.json().get('id')
                
                return True
                
            except Exception as e:
                if attempt == 2:  # Last attempt
                    st.error(f"❌ Auth failed: {str(e)}")
                    return False
                time.sleep(1)  # Brief retry delay
        
        return False

    def upload_and_share_fast(self, file_bytes: bytes, filename: str, team_emails: List[str]) -> Optional[str]:
        """Fast upload and immediate sharing"""
        if not self.access_token or not self.user_id:
            return None
        
        try:
            # Upload file directly to root (faster than creating folder)
            upload_url = f"https://graph.microsoft.com/v1.0/users/{self.user_id}/drive/root/children/{filename}/content"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            
            # Upload with progress
            upload_response = self.session.put(upload_url, headers=headers, data=file_bytes, timeout=60)
            upload_response.raise_for_status()
            
            file_info = upload_response.json()
            file_id = file_info.get('id')
            
            if file_id and team_emails:
                # Immediate sharing (parallel)
                share_url = f"https://graph.microsoft.com/v1.0/users/{self.user_id}/drive/items/{file_id}/invite"
                share_headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                
                share_data = {
                    "recipients": [{"email": email} for email in team_emails],
                    "message": "🚀 Fast C2C AI/ML Job Results - Auto-generated",
                    "requireSignIn": True,
                    "sendInvitation": True,
                    "roles": ["read"]
                }
                
                # Share in background (don't wait)
                try:
                    self.session.post(share_url, headers=share_headers, json=share_data, timeout=30)
                except:
                    pass  # Don't fail if sharing fails
                
                # Get link
                link_url = f"https://graph.microsoft.com/v1.0/users/{self.user_id}/drive/items/{file_id}/createLink"
                link_data = {"type": "view", "scope": "organization"}
                
                try:
                    link_response = self.session.post(link_url, headers=share_headers, json=link_data, timeout=15)
                    link_response.raise_for_status()
                    return link_response.json().get('link', {}).get('webUrl')
                except:
                    pass
            
            return f"https://leapgenai-my.sharepoint.com/personal/{self.user_id}/Documents/{filename}"
            
        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")
            return None


def main():
    """Optimized main application with C2C filtering"""
    
    # Load configuration
    config = get_config()
    client_id = config['client_id']
    client_secret = config['client_secret']
    tenant_id = config['tenant_id']
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>⚡ MULTI-PORTAL C2C AI/ML Job Scraper</h1>
        <p>🚀 7 Job Portals + Lightning-fast scraping + C2C filtering + Auto OneDrive upload + Team sharing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # C2C Filter Info
    st.markdown("""
    <div class="c2c-filter">
        <h3>🎯 C2C Filter Active + Multi-Portal Search</h3>
        <p>🔍 <strong>Portals:</strong> Greenhouse • Lever • Indeed • Dice • RemoteOK • AngelList • Upwork</p>
        <p>🎯 <strong>Filtering for:</strong> C2C, Corp-to-Corp, 1099, Contract roles only</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick config check
    col1, col2, col3 = st.columns(3)
    
    with col1:
        config_ok = all([client_id, client_secret, tenant_id])
        if config_ok:
            st.success("✅ Config Ready")
        else:
            st.error("❌ Config Missing")
    
    with col2:
        target_user = "hemanth.yarraguravagari@leapgen.ai"
        st.info(f"📧 Target: {target_user}")
    
    with col3:
        team_emails = [
            'Parind.Raval@leapgen.ai',
            'Kumar.Konduru@leapgen.ai', 
            'hemanth.yarraguravagari@leapgen.ai'
        ]
        st.info(f"👥 Team: {len(team_emails)} members")
    
    # Main action button
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 MULTI-PORTAL C2C SCRAPE + AUTO UPLOAD", 
                    type="primary", 
                    use_container_width=True,
                    help="Lightning-fast C2C job scraping from 7 job portals with automatic OneDrive upload"):
            
            if not config_ok:
                st.error("❌ Please configure your Microsoft credentials in .env file")
                return
            
            # Speed metrics
            total_start = time.time()
            
            # Phase 1: Fast Scraping with C2C Filter
            st.markdown("""
            <div class="speed-metric">
                <h3>⚡ PHASE 1: MULTI-PORTAL SCRAPING + C2C FILTERING</h3>
                <p>Searching across 7 job portals for C2C opportunities...</p>
            </div>
            """, unsafe_allow_html=True)
            
            scraper = FastJobScraper()
            scrape_start = time.time()
            
            scraper.scrape_all_jobs_fast()
            
            scrape_time = time.time() - scrape_start
            
            if not scraper.jobs_data:
                st.warning("⚠️ No C2C jobs found!")
                return
            
            # Display results
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🎯 Total C2C Jobs", len(scraper.jobs_data))
            with col2:
                st.metric("🕒 Scrape Time", f"{scrape_time:.1f}s")
            with col3:
                total_portals = len(set(job['source'] for job in scraper.jobs_data)) if scraper.jobs_data else 0
                st.metric("🌐 Portals Used", total_portals)
            with col4:
                avg_per_portal = len(scraper.jobs_data) / max(total_portals, 1) if scraper.jobs_data else 0
                st.metric("📊 Avg per Portal", f"{avg_per_portal:.1f}")
            
            # Phase 2: Auto Upload
            st.markdown("""
            <div class="auto-upload-status">
                <h3>☁️ PHASE 2: AUTO ONEDRIVE UPLOAD</h3>
                <p>Uploading C2C jobs and sharing automatically...</p>
            </div>
            """, unsafe_allow_html=True)
            
            upload_start = time.time()
            
            # Create Excel
            excel_bytes = scraper.create_excel_fast()
            
            if excel_bytes:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"multi_portal_c2c_ai_ml_jobs_{timestamp}.xlsx"
                
                # Auto upload with progress
                upload_progress = st.progress(0)
                upload_status = st.empty()
                
                upload_status.text("🔐 Authenticating...")
                upload_progress.progress(0.2)
                
                uploader = FastOneDriveUploader(client_id, client_secret, tenant_id)
                
                if uploader.authenticate_fast(target_user):
                    upload_status.text("☁️ Uploading C2C jobs...")
                    upload_progress.progress(0.6)
                    
                    share_link = uploader.upload_and_share_fast(excel_bytes, filename, team_emails)
                    
                    upload_time = time.time() - upload_start
                    total_time = time.time() - total_start
                    
                    upload_progress.progress(1.0)
                    upload_status.text("✅ Upload complete!")
                    
                    # Success metrics
                    st.markdown("""
                    <div class="auto-upload-status">
                        <h2>🎉 SUCCESS!</h2>
                        <p>C2C jobs uploaded and shared automatically</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Performance metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("🕒 Upload Time", f"{upload_time:.1f}s")
                    with col2:
                        st.metric("⏱️ Total Time", f"{total_time:.1f}s")
                    with col3:
                        st.metric("📧 Team Shared", len(team_emails))
                    with col4:
                        st.metric("📁 File Size", f"{len(excel_bytes)/1024:.1f} KB")
                    
                    # OneDrive link
                    if share_link:
                        st.markdown(f"""
                        <div style="background: #e8f5e8; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                            <h3>🔗 OneDrive Link (Auto-generated):</h3>
                            <a href="{share_link}" target="_blank" style="color: #0066cc; font-size: 16px; text-decoration: none;">
                                📂 Open C2C Jobs in OneDrive →
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Download option
                    st.download_button(
                        label="⬇️ Download C2C Jobs Backup",
                        data=excel_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    # Quick preview with C2C indicators
                    if st.checkbox("📋 Show C2C job preview"):
                        df = pd.DataFrame(scraper.jobs_data)
                        preview_df = df[['company', 'job_title', 'location', 'source', 'employment_type']].head(20)
                        st.dataframe(preview_df, use_container_width=True)
                        
                        # Show some C2C indicators found
                        st.subheader("🎯 C2C Keywords Found:")
                        c2c_indicators = []
                        for job in scraper.jobs_data[:5]:  # Show first 5 jobs
                            desc = job.get('job_description', '').lower()
                            emp_type = job.get('employment_type', '').lower()
                            text_to_check = f"{desc} {emp_type}"
                            
                            found_keywords = [kw for kw in scraper.c2c_keywords if kw in text_to_check]
                            if found_keywords:
                                c2c_indicators.extend(found_keywords)
                        
                        unique_indicators = list(set(c2c_indicators))
                        if unique_indicators:
                            st.info(f"**Found C2C indicators:** {', '.join(unique_indicators[:10])}")
                else:
                    st.error("❌ OneDrive authentication failed")
            else:
                st.error("❌ Excel creation failed")
    
    # Auto-refresh notice
    st.markdown("---")
    st.info("💡 **Tip**: This app searches across 7 major job portals, automatically filters for C2C roles, uploads to OneDrive and shares with your team. Check your OneDrive for the latest multi-portal C2C job results!")
    
    # Job Portal Info
    st.markdown("""
    ### 🌐 **Supported Job Portals:**
    - 🏢 **Greenhouse** - Top tech companies
    - ⚡ **Lever** - High-growth startups  
    - 🔍 **Indeed** - Largest job board
    - 🎲 **Dice** - Tech-focused platform
    - 🌐 **RemoteOK** - Remote opportunities
    - 👼 **AngelList** - Startup ecosystem
    - 💼 **Upwork** - Freelance projects
    """)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>⚡ <strong>Multi-Portal C2C AI/ML Job Scraper</strong> | 7 Portals • C2C Filtering • Automated Sharing</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
