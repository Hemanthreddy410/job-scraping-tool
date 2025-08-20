#!/usr/bin/env python3
"""
Test OneDrive credentials
"""

import os
from dotenv import load_dotenv
from onedrive_uploader import OneDriveUploader

# Load environment variables
load_dotenv()

def test_credentials():
    print("🔧 Testing OneDrive Credentials...")
    print("=" * 40)
    
    # Get credentials
    client_id = os.getenv('MICROSOFT_CLIENT_ID')
    client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
    tenant_id = os.getenv('MICROSOFT_TENANT_ID')
    
    print(f"Client ID: {client_id[:8] if client_id else 'MISSING'}...")
    print(f"Client Secret: {client_secret[:8] if client_secret else 'MISSING'}...")
    print(f"Tenant ID: {tenant_id[:8] if tenant_id else 'MISSING'}...")
    print()
    
    if not all([client_id, client_secret, tenant_id]):
        print("❌ Some credentials are missing!")
        return False
    
    print("✅ All credentials present")
    print()
    
    # Test authentication
    print("🔑 Testing authentication...")
    uploader = OneDriveUploader(client_id, client_secret, tenant_id)
    
    if uploader.get_access_token():
        print("✅ Authentication successful!")
        return True
    else:
        print("❌ Authentication failed!")
        print("Possible issues:")
        print("- Wrong credentials")
        print("- App doesn't have Files.ReadWrite.All permission")
        print("- Admin consent not granted")
        return False

if __name__ == "__main__":
    test_credentials()