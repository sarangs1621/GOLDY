#!/usr/bin/env python3
"""
Create test inventory headers for testing the inventory headers API endpoint
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

def authenticate():
    """Authenticate and get JWT token"""
    session = requests.Session()
    
    try:
        response = session.post(f"{BASE_URL}/auth/login", json={
            "username": USERNAME,
            "password": PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            session.headers.update({"Authorization": f"Bearer {token}"})
            print(f"✅ Successfully authenticated as {USERNAME}")
            return session
        else:
            print(f"❌ Failed to authenticate: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return None

def create_inventory_headers(session):
    """Create test inventory headers"""
    
    test_headers = [
        {"name": "Gold Chains"},
        {"name": "Gold Rings"},
        {"name": "Gold Earrings"},
        {"name": "Gold Bracelets"},
        {"name": "Gold Necklaces"}
    ]
    
    created_headers = []
    
    for header_data in test_headers:
        try:
            response = session.post(f"{BASE_URL}/inventory/headers", json=header_data)
            
            if response.status_code == 200:
                header = response.json()
                created_headers.append(header)
                print(f"✅ Created inventory header: {header.get('name')} (ID: {header.get('id')})")
            else:
                print(f"❌ Failed to create header '{header_data['name']}': {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating header '{header_data['name']}': {str(e)}")
    
    return created_headers

def main():
    print("CREATING TEST INVENTORY HEADERS")
    print("Backend URL:", BASE_URL)
    print("Authentication:", f"{USERNAME}/***")
    print("="*80)
    
    # Authenticate
    session = authenticate()
    if not session:
        print("❌ Authentication failed. Cannot proceed.")
        return False
    
    # Create inventory headers
    created_headers = create_inventory_headers(session)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Created {len(created_headers)} inventory headers:")
    
    for header in created_headers:
        print(f"  - {header.get('name')} (ID: {header.get('id')})")
    
    if created_headers:
        print("\n✅ Test inventory headers created successfully!")
        print("✅ Ready to test inventory headers API endpoint")
        return True
    else:
        print("\n❌ No inventory headers were created")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)