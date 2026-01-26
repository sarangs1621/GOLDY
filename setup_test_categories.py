#!/usr/bin/env python3
"""
Setup Test Data for Category Dropdown Testing
Creates inventory headers (categories) for testing the dropdown fix
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

def setup_test_categories():
    """Create test inventory categories"""
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{BASE_URL}/auth/login", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return False
    
    data = response.json()
    token = data.get("access_token")
    csrf_token = data.get("csrf_token")
    
    session.headers.update({"Authorization": f"Bearer {token}"})
    if csrf_token:
        session.headers.update({"X-CSRF-Token": csrf_token})
    
    print("✅ Authenticated successfully")
    
    # Test categories to create (matching the review request examples)
    test_categories = [
        {"name": "Chain"},
        {"name": "Gold Rings"},
        {"name": "Gold Earrings"},
        {"name": "Gold Necklace"},
        {"name": "Gold Bracelet"}
    ]
    
    created_count = 0
    
    for category in test_categories:
        try:
            response = session.post(f"{BASE_URL}/inventory/headers", json=category)
            
            if response.status_code == 200:
                created_data = response.json()
                print(f"✅ Created category: {category['name']} (ID: {created_data.get('id')})")
                created_count += 1
            else:
                print(f"❌ Failed to create {category['name']}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating {category['name']}: {str(e)}")
    
    print(f"\n✅ Created {created_count}/{len(test_categories)} test categories")
    
    # Verify categories were created
    response = session.get(f"{BASE_URL}/inventory/headers")
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        print(f"✅ Verification: {len(items)} total categories now available")
        
        for item in items:
            print(f"   - {item.get('name')} (ID: {item.get('id')})")
        
        return len(items) > 0
    else:
        print(f"❌ Failed to verify categories: {response.status_code}")
        return False

if __name__ == "__main__":
    success = setup_test_categories()
    sys.exit(0 if success else 1)