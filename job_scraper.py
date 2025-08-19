#!/usr/bin/env python3
"""
Job Scraping and Export Tool
Scrapes AI Engineer, Data Engineer, and Data Scientist roles from Greenhouse and Lever APIs
Exports to Excel and uploads to OneDrive
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Optional
import re
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.target_roles = [
            'AI Engineer', 'Artificial Intelligence Engineer', 'Machine Learning Engineer',
            'Data Engineer', 'Senior Data Engineer', 'Principal Data Engineer',
            'Data Scientist', 'Senior Data Scientist', 'Principal Data Scientist'
        ]
        self.usa_locations = [
            'United States', 'USA', 'US', 'Remote - US', 'Remote (US)',
            'New York', 'San Francisco', 'Los Angeles', 'Chicago', 'Boston',
            'Seattle', 'Austin', 'Denver', 'Atlanta', 'Remote'
        ]
        self.jobs_data = []

    def clean_text(self, text: str) -> str:
        """Clean and normalize text data"""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()

    def is_target_role(self, job_title: str) -> bool:
        """Check if job title matches target roles"""
        job_title_lower = job_title.lower()
        return any(
            role.lower() in job_title_lower 
            for role in self.target_roles
        )

    def is_usa_location(self, location: str) -> bool:
        """Check if location is in USA"""
        if not location:
            return False
        location_lower = location.lower()
        return any(
            usa_loc.lower() in location_lower 
            for usa_loc in self.usa_locations
        )

    def scrape_greenhouse_jobs(self) -> List[Dict]:
        """Scrape jobs from Greenhouse API"""
        logger.info("Starting Greenhouse job scraping...")
        greenhouse_jobs = []
        
        # List of known companies using Greenhouse (you can expand this)
        greenhouse_companies = [
            'airbnb', 'stripe', 'notion', 'figma', 'databricks', 
            'snowflake', 'coinbase', 'instacart', 'robinhood'
        ]
        
        for company in greenhouse_companies:
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    jobs = response.json().get('jobs', [])
                    
                    for job in jobs:
                        job_title = job.get('title', '')
                        location = job.get('location', {}).get('name', '')
                        
                        if (self.is_target_role(job_title) and 
                            self.is_usa_location(location)):
                            
                            greenhouse_jobs.append({
                                'company': company.title(),
                                'job_title': self.clean_text(job_title),
                                'location': self.clean_text(location),
                                'job_url': job.get('absolute_url', ''),
                                'job_description': self.clean_text(job.get('content', '')),
                                'posted_date': job.get('updated_at', ''),
                                'source': 'Greenhouse',
                                'job_id': str(job.get('id', ''))
                            })
                    
                    logger.info(f"Found {len([j for j in jobs if self.is_target_role(j.get('title', '')) and self.is_usa_location(j.get('location', {}).get('name', ''))])} relevant jobs from {company}")
                    
                elif response.status_code == 404:
                    logger.warning(f"Company {company} not found on Greenhouse")
                else:
                    logger.error(f"Error fetching {company}: {response.status_code}")
                    
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping {company} from Greenhouse: {str(e)}")
                continue
        
        logger.info(f"Total Greenhouse jobs found: {len(greenhouse_jobs)}")
        return greenhouse_jobs

    def scrape_lever_jobs(self) -> List[Dict]:
        """Scrape jobs from Lever API"""
        logger.info("Starting Lever job scraping...")
        lever_jobs = []
        
        # List of known companies using Lever (you can expand this)
        lever_companies = [
            'netflix', 'uber', 'shopify', 'zoom', 'atlassian',
            'spotify', 'pinterest', 'reddit', 'discord'
        ]
        
        for company in lever_companies:
            try:
                url = f"https://api.lever.co/v0/postings/{company}"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    jobs = response.json()
                    
                    for job in jobs:
                        job_title = job.get('text', '')
                        location = job.get('categories', {}).get('location', '')
                        
                        if (self.is_target_role(job_title) and 
                            self.is_usa_location(location)):
                            
                            lever_jobs.append({
                                'company': company.title(),
                                'job_title': self.clean_text(job_title),
                                'location': self.clean_text(location),
                                'job_url': job.get('hostedUrl', ''),
                                'job_description': self.clean_text(job.get('description', '')),
                                'posted_date': job.get('createdAt', ''),
                                'source': 'Lever',
                                'job_id': job.get('id', '')
                            })
                    
                    logger.info(f"Found {len([j for j in jobs if self.is_target_role(j.get('text', '')) and self.is_usa_location(j.get('categories', {}).get('location', ''))])} relevant jobs from {company}")
                    
                elif response.status_code == 404:
                    logger.warning(f"Company {company} not found on Lever")
                else:
                    logger.error(f"Error fetching {company}: {response.status_code}")
                    
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping {company} from Lever: {str(e)}")
                continue
        
        logger.info(f"Total Lever jobs found: {len(lever_jobs)}")
        return lever_jobs

    def scrape_all_jobs(self) -> None:
        """Scrape jobs from all sources"""
        logger.info("Starting comprehensive job scraping...")
        
        # Scrape from both sources
        greenhouse_jobs = self.scrape_greenhouse_jobs()
        lever_jobs = self.scrape_lever_jobs()
        
        # Combine all jobs
        self.jobs_data = greenhouse_jobs + lever_jobs
        
        # Remove duplicates based on job_title and company
        seen = set()
        unique_jobs = []
        for job in self.jobs_data:
            key = (job['company'].lower(), job['job_title'].lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        self.jobs_data = unique_jobs
        logger.info(f"Total unique jobs after deduplication: {len(self.jobs_data)}")

    def create_excel_file(self, filename: str = None) -> str:
        """Create Excel file with job data"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_scraping_results_{timestamp}.xlsx"
        
        logger.info(f"Creating Excel file: {filename}")
        
        # Create DataFrame
        df = pd.DataFrame(self.jobs_data)
        
        if df.empty:
            logger.warning("No job data to export")
            return filename
        
        # Reorder columns
        column_order = [
            'company', 'job_title', 'location', 'job_url', 
            'posted_date', 'source', 'job_id', 'job_description'
        ]
        df = df.reindex(columns=column_order)
        
        # Create workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Job Scraping Results"
        
        # Define styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        # Write headers
        headers = [
            'Company', 'Job Title', 'Location', 'Job URL', 
            'Posted Date', 'Source', 'Job ID', 'Job Description'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
        
        # Write data
        for row, job in enumerate(self.jobs_data, 2):
            ws.cell(row=row, column=1, value=job.get('company', ''))
            ws.cell(row=row, column=2, value=job.get('job_title', ''))
            ws.cell(row=row, column=3, value=job.get('location', ''))
            ws.cell(row=row, column=4, value=job.get('job_url', ''))
            ws.cell(row=row, column=5, value=job.get('posted_date', ''))
            ws.cell(row=row, column=6, value=job.get('source', ''))
            ws.cell(row=row, column=7, value=job.get('job_id', ''))
            ws.cell(row=row, column=8, value=job.get('job_description', ''))
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Add summary sheet
        summary_ws = wb.create_sheet("Summary")
        summary_data = [
            ["Metric", "Value"],
            ["Total Jobs Found", len(self.jobs_data)],
            ["Jobs by Source", ""],
            ["  - Greenhouse", len([j for j in self.jobs_data if j['source'] == 'Greenhouse'])],
            ["  - Lever", len([j for j in self.jobs_data if j['source'] == 'Lever'])],
            ["Jobs by Role Type", ""],
            ["  - AI Engineer", len([j for j in self.jobs_data if 'ai' in j['job_title'].lower() or 'artificial intelligence' in j['job_title'].lower()])],
            ["  - Data Engineer", len([j for j in self.jobs_data if 'data engineer' in j['job_title'].lower()])],
            ["  - Data Scientist", len([j for j in self.jobs_data if 'data scientist' in j['job_title'].lower()])],
            ["Scraping Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        for row, (metric, value) in enumerate(summary_data, 1):
            summary_ws.cell(row=row, column=1, value=metric)
            summary_ws.cell(row=row, column=2, value=value)
            if row == 1:  # Header row
                summary_ws.cell(row=row, column=1).font = header_font
                summary_ws.cell(row=row, column=2).font = header_font
        
        # Save workbook
        wb.save(filename)
        logger.info(f"Excel file created successfully: {filename}")
        return filename

class OneDriveUploader:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.access_token = None

    def get_access_token(self) -> bool:
        """Get access token for Microsoft Graph API"""
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            logger.info("Successfully obtained access token")
            return True
            
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return False

    def upload_file(self, file_path: str, onedrive_folder: str = "Job Scraping Results") -> Optional[str]:
        """Upload file to OneDrive"""
        if not self.access_token:
            logger.error("No access token available")
            return None
        
        try:
            # Create folder if it doesn't exist
            folder_url = f"https://graph.microsoft.com/v1.0/me/drive/root/children"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            folder_data = {
                "name": onedrive_folder,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            
            folder_response = requests.post(folder_url, headers=headers, json=folder_data)
            
            # Upload file
            filename = Path(file_path).name
            upload_url = f"https://graph.microsoft.com/v1.0/users/hemanth.yarraguravagari@leapgen.ai/drive/root:/{onedrive_folder}/{filename}:/content"
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            upload_headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            
            response = requests.put(upload_url, headers=upload_headers, data=file_content)
            response.raise_for_status()
            
            file_info = response.json()
            file_id = file_info.get('id')
            
            logger.info(f"File uploaded successfully to OneDrive: {filename}")
            return file_id
            
        except Exception as e:
            logger.error(f"Error uploading file to OneDrive: {str(e)}")
            return None

    def share_with_users(self, file_id: str, user_emails: List[str]) -> bool:
        """Share file with specified users"""
        if not self.access_token or not file_id:
            return False
        
        try:
            share_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/invite"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            for email in user_emails:
                share_data = {
                    "recipients": [{"email": email}],
                    "message": "Job scraping results - shared by automated system",
                    "requireSignIn": True,
                    "sendInvitation": True,
                    "roles": ["read"]
                }
                
                response = requests.post(share_url, headers=headers, json=share_data)
                
                if response.status_code == 200:
                    logger.info(f"File shared successfully with {email}")
                else:
                    logger.error(f"Error sharing with {email}: {response.status_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sharing file: {str(e)}")
            return False

def main():
    """Main execution function"""
    logger.info("Starting Job Scraping and Export Tool")
    
    # Initialize scraper
    scraper = JobScraper()
    
    # Scrape jobs
    scraper.scrape_all_jobs()
    
    if not scraper.jobs_data:
        logger.warning("No jobs found. Exiting.")
        return
    
    # Create Excel file
    excel_filename = scraper.create_excel_file()
    
    # OneDrive configuration (replace with actual credentials)
    # These should be stored securely (environment variables, config file, etc.)
    ONEDRIVE_CONFIG = {
    'client_id': os.getenv('MICROSOFT_CLIENT_ID'),
    'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET'),
    'tenant_id': os.getenv('MICROSOFT_TENANT_ID')
   }
    # Initialize OneDrive uploader
    uploader = OneDriveUploader(**ONEDRIVE_CONFIG)
    
    # Get access token and upload
    if uploader.get_access_token():
        file_id = uploader.upload_file(excel_filename)
        
        if file_id:
            # Share with Parind and Kumar
            user_emails = ['Parind.Raval@leapgen.ai', 'Kumar.Konduru@leapgen.ai', 'hemanth.yarraguravagari@leapgen.ai', 'Anurag.D@leapgen.ai']  # Replace with actual emails
            uploader.share_with_users(file_id, user_emails)
    
    logger.info("Job scraping and export process completed")
    print(f"\nSummary:")
    print(f"Total jobs found: {len(scraper.jobs_data)}")
    print(f"Excel file created: {excel_filename}")
    print(f"File uploaded to OneDrive: {'Yes' if 'file_id' in locals() else 'No'}")

if __name__ == "__main__":
    main()