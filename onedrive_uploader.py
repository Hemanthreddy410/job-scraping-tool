#!/usr/bin/env python3
"""
Simple OneDrive Uploader
"""

import requests
import logging
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class OneDriveUploader:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.access_token = None

    def get_access_token(self) -> bool:
        """Get access token from Microsoft"""
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            if self.access_token:
                logger.info("Got access token successfully")
                return True
            else:
                logger.error("No access token in response")
                return False
                
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return False

    def upload_file(self, file_path: str, folder_name: str = "Job Results") -> Optional[str]:
        """Upload file to OneDrive"""
        if not self.access_token:
            logger.error("No access token")
            return None
        
        try:
            file_path_obj = Path(file_path)
            filename = file_path_obj.name
            
            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            # Create folder first
            self._create_folder(folder_name)
            
            # Upload file
            upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder_name}/{filename}:/content"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            response = requests.put(upload_url, headers=headers, data=file_content, timeout=60)
            response.raise_for_status()
            
            file_info = response.json()
            file_id = file_info.get('id')
            
            logger.info(f"File uploaded: {filename}")
            return file_id
            
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return None

    def _create_folder(self, folder_name: str):
        """Create folder in OneDrive"""
        try:
            url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            folder_data = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            
            response = requests.post(url, headers=headers, json=folder_data, timeout=30)
            # Don't raise error if folder already exists
            
        except Exception as e:
            logger.warning(f"Folder creation warning: {str(e)}")

    def share_with_users(self, file_id: str, user_emails: List[str]) -> bool:
        """Share file with users"""
        if not self.access_token or not file_id:
            return False
        
        try:
            share_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/invite"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            for email in user_emails:
                if not email or not email.strip():
                    continue
                    
                share_data = {
                    "recipients": [{"email": email.strip()}],
                    "message": "AI/ML Job search results",
                    "requireSignIn": True,
                    "sendInvitation": True,
                    "roles": ["read"]
                }
                
                try:
                    response = requests.post(share_url, headers=headers, json=share_data, timeout=30)
                    if response.status_code in [200, 201]:
                        logger.info(f"Shared with {email}")
                    else:
                        logger.warning(f"Share failed for {email}")
                        
                except Exception as e:
                    logger.warning(f"Share error for {email}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Share error: {str(e)}")
            return False