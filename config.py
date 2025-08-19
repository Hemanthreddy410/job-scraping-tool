# config.py - Configuration file for the job scraping tool

import os
from typing import List, Dict

class Config:
    """Configuration class for job scraping tool"""
    
    # API Rate Limiting
    REQUEST_DELAY = 1  # seconds between API requests
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    
    # Job filtering criteria
    TARGET_ROLES = [
        'AI Engineer', 'Artificial Intelligence Engineer', 'Machine Learning Engineer',
        'ML Engineer', 'AI/ML Engineer', 'Applied AI Engineer',
        'Data Engineer', 'Senior Data Engineer', 'Principal Data Engineer',
        'Staff Data Engineer', 'Lead Data Engineer',
        'Data Scientist', 'Senior Data Scientist', 'Principal Data Scientist',
        'Staff Data Scientist', 'Lead Data Scientist', 'Applied Data Scientist'
    ]
    
    USA_LOCATIONS = [
        'United States', 'USA', 'US', 'Remote - US', 'Remote (US)',
        'New York', 'San Francisco', 'Los Angeles', 'Chicago', 'Boston',
        'Seattle', 'Austin', 'Denver', 'Atlanta', 'Portland', 'Miami',
        'Dallas', 'Phoenix', 'San Diego', 'Remote', 'Anywhere in US'
    ]
    
    # Company lists for scraping
    GREENHOUSE_COMPANIES = [
        'airbnb', 'stripe', 'notion', 'figma', 'databricks', 'snowflake',
        'coinbase', 'instacart', 'robinhood', 'doordash', 'lyft',
        'square', 'twitch', 'gitlab', 'hashicorp', 'datadog'
    ]
    
    LEVER_COMPANIES = [
        'netflix', 'uber', 'shopify', 'zoom', 'atlassian', 'spotify',
        'pinterest', 'reddit', 'discord', 'box', 'lever', 'mixpanel',
        'pagerduty', 'segment', 'twilio', 'zendesk'
    ]
    
    # OneDrive settings
    ONEDRIVE_FOLDER_NAME = "Job Scraping Results"
    SHARE_USERS = ['Parind.Raval@leapgen.ai', 'Kumar.Konduru@leapgen.ai', 'hemanth.yarraguravagari@leapgen.ai']
    
    # File settings
    OUTPUT_FILENAME_TEMPLATE = "job_scraping_results_{timestamp}.xlsx"
    
    # Microsoft Graph API credentials (should be loaded from environment variables)
    @staticmethod
    def get_onedrive_config() -> Dict[str, str]:
        return {
            'client_id': os.getenv('MICROSOFT_CLIENT_ID', 'YOUR_CLIENT_ID'),
            'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET', 'YOUR_CLIENT_SECRET'),
            'tenant_id': os.getenv('MICROSOFT_TENANT_ID', 'YOUR_TENANT_ID')
        }

# Save these files
def create_project_files():
    """Create all necessary project files"""
    
    # Create requirements.txt
    with open('requirements.txt', 'w') as f:
        f.write(REQUIREMENTS.strip())
    
    # Create .env template
    with open('.env.template', 'w') as f:
        f.write(ENV_TEMPLATE.strip())
    
    # Create setup.py
    with open('setup.py', 'w') as f:
        f.write(SETUP_PY.strip())
    
    print("Project files created successfully!")
    print("Files created:")
    print("- requirements.txt")
    print("- .env.template")
    print("- setup.py")
    print("- config.py (this file)")

if __name__ == "__main__":
    create_project_files()