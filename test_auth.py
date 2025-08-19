#!/usr/bin/env python3
"""
Test OneDrive Authentication
Quick test to verify client secret and permissions
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Get credentials
client_id = os.getenv('MICROSOFT_CLIENT_ID')
client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
tenant_id = os.getenv('MICROSOFT_TENANT_ID')

print("🔍 TESTING ONEDRIVE AUTHENTICATION")
print("=" * 50)
print(f"Client ID: {client_id}")
print(f"Client Secret: {client_secret[:10]}...")
print(f"Tenant ID: {tenant_id}")
print()

# Test authentication
url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': 'https://graph.microsoft.com/.default',
    'grant_type': 'client_credentials'
}

print("🔄 Testing authentication...")
try:
    response = requests.post(url, data=data)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        print("✅ SUCCESS! Authentication working!")
        print(f"Token received: {access_token[:20]}...")
        
        # Test a simple Graph API call
        print("\n🔄 Testing Graph API access...")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Test user profile access
        graph_response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        print(f"Graph API Status: {graph_response.status_code}")
        
        if graph_response.status_code == 200:
            print("✅ Graph API access working!")
        else:
            print("❌ Graph API access failed")
            print(f"Response: {graph_response.text}")
        
    else:
        print("❌ AUTHENTICATION FAILED!")
        print(f"Response: {response.text}")
        
        # Parse error
        try:
            error_data = response.json()
            error_desc = error_data.get('error_description', 'Unknown error')
            print(f"Error: {error_desc}")
        except:
            print("Could not parse error response")

except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print("\n" + "=" * 50)