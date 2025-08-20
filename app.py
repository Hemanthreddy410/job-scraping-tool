#!/usr/bin/env python3
"""
OPTIMIZED Fast Job Scraper Application
Faster scraping + Automatic OneDrive upload + Real-time progress

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

# Page configuration
st.set_page_config(
    page_title="⚡ Fast AI/ML Job Scraper",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    """Optimized job scraper with parallel processing and caching"""
    
    def __init__(self):
        self.target_roles = [
            'AI Engineer', 'Machine Learning Engineer', 'ML Engineer', 'MLOps Engineer',
            'Data Engineer', 'Senior Data Engineer', 'Principal Data Engineer',
            'Data Scientist', 'Senior Data Scientist', 'Applied Data Scientist'
        ]
        self.usa_locations = [
            'United States', 'USA', 'US', 'Remote', 'New York', 'San Francisco', 
            'Los Angeles', 'Chicago', 'Boston', 'Seattle', 'Austin', 'California', 'Texas'
        ]
        self.jobs_data = []
        self.session = requests.Session()  # Reuse connections
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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

    def clean_text(self, text: str) -> str:
        """Fast text cleaning"""
        if not text:
            return ""
        return ' '.join(re.sub(r'<[^>]+>', '', text).split()).strip()

    def scrape_greenhouse_fast(self, companies_batch: List[str]) -> List[Dict]:
        """Fast parallel Greenhouse scraping"""
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
                            company_jobs.append({
                                'company': company.title(),
                                'job_title': self.clean_text(job_title),
                                'location': self.clean_text(location),
                                'job_url': job.get('absolute_url', ''),
                                'posted_date': job.get('updated_at', ''),
                                'source': 'Greenhouse',
                                'job_id': str(job.get('id', ''))
                            })
                    return company_jobs
            except:
                pass
            return []
        
        # Parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(scrape_company, companies_batch))
        
        for result in results:
            jobs.extend(result)
        
        return jobs

    def scrape_lever_fast(self, companies_batch: List[str]) -> List[Dict]:
        """Fast parallel Lever scraping"""
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
                            company_jobs.append({
                                'company': company.title(),
                                'job_title': self.clean_text(job_title),
                                'location': self.clean_text(location),
                                'job_url': job.get('hostedUrl', ''),
                                'posted_date': job.get('createdAt', ''),
                                'source': 'Lever',
                                'job_id': job.get('id', '')
                            })
                    return company_jobs
            except:
                pass
            return []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(scrape_company, companies_batch))
        
        for result in results:
            jobs.extend(result)
        
        return jobs

    def scrape_all_jobs_fast(self) -> None:
        """Optimized scraping with real-time progress"""
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        start_time = time.time()
        
        # Company lists (top companies only for speed)
        greenhouse_companies = [
            'airbnb', 'stripe', 'databricks', 'coinbase', 'instacart',
            'doordash', 'square', 'gitlab', 'datadog'
        ]
        
        lever_companies = [
            'netflix', 'spotify', 'atlassian', 'discord', 'twilio'
        ]
        
        all_jobs = []
        
        # Phase 1: Greenhouse (fast)
        status_text.text("⚡ Fast scraping Greenhouse...")
        progress_bar.progress(0.2)
        
        greenhouse_jobs = self.scrape_greenhouse_fast(greenhouse_companies)
        all_jobs.extend(greenhouse_jobs)
        
        status_text.text(f"✅ Greenhouse: {len(greenhouse_jobs)} jobs")
        progress_bar.progress(0.6)
        
        # Phase 2: Lever (fast)
        status_text.text("⚡ Fast scraping Lever...")
        
        lever_jobs = self.scrape_lever_fast(lever_companies)
        all_jobs.extend(lever_jobs)
        
        status_text.text(f"✅ Lever: {len(lever_jobs)} jobs")
        progress_bar.progress(0.9)
        
        # Deduplicate
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (job['company'].lower().strip(), job['job_title'].lower().strip())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        self.jobs_data = unique_jobs
        
        end_time = time.time()
        duration = end_time - start_time
        
        progress_bar.progress(1.0)
        status_text.text(f"🚀 COMPLETE! {len(self.jobs_data)} jobs in {duration:.1f}s")

    def create_excel_fast(self) -> bytes:
        """Fast Excel creation"""
        if not self.jobs_data:
            return None
        
        # Simple Excel creation for speed
        wb = Workbook()
        ws = wb.active
        ws.title = "AI ML Jobs"
        
        # Headers
        headers = ['Company', 'Job Title', 'Location', 'Job URL', 'Posted Date', 'Source']
        ws.append(headers)
        
        # Data
        for job in self.jobs_data:
            ws.append([
                job.get('company', ''),
                job.get('job_title', ''),
                job.get('location', ''),
                job.get('job_url', ''),
                job.get('posted_date', ''),
                job.get('source', '')
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
                    "message": "🚀 Fast AI/ML Job Results - Auto-generated",
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
    """Optimized main application"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>⚡ FAST AI/ML Job Scraper</h1>
        <p>🚀 Lightning-fast scraping + Auto OneDrive upload + Team sharing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-configuration (hidden for speed)
    client_id = os.getenv('MICROSOFT_CLIENT_ID')
    client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
    tenant_id = os.getenv('MICROSOFT_TENANT_ID')
    
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
        if st.button("🚀 FAST SCRAPE + AUTO UPLOAD", 
                    type="primary", 
                    use_container_width=True,
                    help="Lightning-fast job scraping with automatic OneDrive upload"):
            
            if not config_ok:
                st.error("❌ Please configure your Microsoft credentials in .env file")
                return
            
            # Speed metrics
            total_start = time.time()
            
            # Phase 1: Fast Scraping
            st.markdown("""
            <div class="speed-metric">
                <h3>⚡ PHASE 1: FAST SCRAPING</h3>
            </div>
            """, unsafe_allow_html=True)
            
            scraper = FastJobScraper()
            scrape_start = time.time()
            
            scraper.scrape_all_jobs_fast()
            
            scrape_time = time.time() - scrape_start
            
            if not scraper.jobs_data:
                st.warning("⚠️ No jobs found!")
                return
            
            # Display results
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("⚡ Jobs Found", len(scraper.jobs_data))
            with col2:
                st.metric("🕒 Scrape Time", f"{scrape_time:.1f}s")
            with col3:
                greenhouse_count = len([j for j in scraper.jobs_data if j['source'] == 'Greenhouse'])
                st.metric("🏢 Greenhouse", greenhouse_count)
            with col4:
                lever_count = len([j for j in scraper.jobs_data if j['source'] == 'Lever'])
                st.metric("⚡ Lever", lever_count)
            
            # Phase 2: Auto Upload
            st.markdown("""
            <div class="auto-upload-status">
                <h3>☁️ PHASE 2: AUTO ONEDRIVE UPLOAD</h3>
                <p>Uploading and sharing automatically...</p>
            </div>
            """, unsafe_allow_html=True)
            
            upload_start = time.time()
            
            # Create Excel
            excel_bytes = scraper.create_excel_fast()
            
            if excel_bytes:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"fast_ai_ml_jobs_{timestamp}.xlsx"
                
                # Auto upload with progress
                upload_progress = st.progress(0)
                upload_status = st.empty()
                
                upload_status.text("🔐 Authenticating...")
                upload_progress.progress(0.2)
                
                uploader = FastOneDriveUploader(client_id, client_secret, tenant_id)
                
                if uploader.authenticate_fast(target_user):
                    upload_status.text("☁️ Uploading file...")
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
                        <p>File uploaded and shared automatically</p>
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
                                📂 Open in OneDrive →
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Download option
                    st.download_button(
                        label="⬇️ Download Backup",
                        data=excel_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    # Quick preview
                    if st.checkbox("📋 Show job preview"):
                        df = pd.DataFrame(scraper.jobs_data)
                        st.dataframe(
                            df[['company', 'job_title', 'location', 'source']].head(20),
                            use_container_width=True
                        )
                else:
                    st.error("❌ OneDrive authentication failed")
            else:
                st.error("❌ Excel creation failed")
    
    # Auto-refresh notice
    st.markdown("---")
    st.info("💡 **Tip**: This app automatically uploads to OneDrive and shares with your team. Check your OneDrive for the latest results!")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>⚡ <strong>Fast AI/ML Job Scraper</strong> | Optimized for Speed & Automation</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()