#!/usr/bin/env python3
"""
Test Cookie-Based JWT Authentication
Tests Phase 1 of Security Hardening
"""

import requests
import sys

BACKEND_URL = "https://decimal-precision.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_cookie_auth():
    """Test cookie-based authentication flow"""
    print("=" * 80)
    print("TESTING COOKIE-BASED JWT AUTHENTICATION")
    print("=" * 80)
    
    # Create a session to persist cookies
    session = requests.Session()
    
    # Test 1: Login and verify cookie is set
    print("\n[TEST 1] Login - Verify HttpOnly Cookie is Set")
    print("-" * 80)
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = session.post(f"{API_BASE}/auth/login", json=login_data)
    
    if response.status_code == 200:
        print(f"✅ Login successful: {response.status_code}")
        
        # Check if cookie is set
        if 'access_token' in session.cookies:
            print(f"✅ Cookie 'access_token' is set")
            cookie = session.cookies.get('access_token')
            print(f"   Cookie value (first 50 chars): {cookie[:50]}...")
        else:
            print("❌ Cookie 'access_token' NOT found in response")
            print(f"   Available cookies: {list(session.cookies.keys())}")
        
        # Check response body
        data = response.json()
        if 'user' in data:
            print(f"✅ User data received: {data['user']['username']} ({data['user']['role']})")
        else:
            print("❌ User data not in response")
            
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Test 2: Access protected endpoint using cookie (no Authorization header)
    print("\n[TEST 2] Access Protected Endpoint - Using Cookie Only")
    print("-" * 80)
    
    # Make sure we don't send Authorization header
    if 'Authorization' in session.headers:
        del session.headers['Authorization']
    
    response = session.get(f"{API_BASE}/auth/me")
    
    if response.status_code == 200:
        print(f"✅ Protected endpoint accessed successfully: {response.status_code}")
        data = response.json()
        print(f"✅ Current user: {data['username']} ({data['role']})")
        print(f"   Permissions count: {len(data.get('permissions', []))}")
    else:
        print(f"❌ Failed to access protected endpoint: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Test 3: Verify cookie attributes (security check)
    print("\n[TEST 3] Verify Cookie Security Attributes")
    print("-" * 80)
    
    cookie_obj = None
    for cookie in session.cookies:
        if cookie.name == 'access_token':
            cookie_obj = cookie
            break
    
    if cookie_obj:
        print(f"✅ Cookie found: {cookie_obj.name}")
        print(f"   Path: {cookie_obj.path}")
        print(f"   Domain: {cookie_obj.domain or 'Not set (same domain)'}")
        print(f"   Secure: {cookie_obj.secure} {'✅' if cookie_obj.secure else '❌ WARNING: Should be True'}")
        print(f"   HttpOnly: {cookie_obj.has_nonstandard_attr('HttpOnly') or 'HttpOnly' in str(cookie_obj)} (Cannot verify from client)")
        print(f"   SameSite: {cookie_obj.get_nonstandard_attr('samesite', 'not set')}")
        
        # Check expiry
        if cookie_obj.expires:
            from datetime import datetime
            expiry = datetime.fromtimestamp(cookie_obj.expires)
            print(f"   Expires: {expiry} (Max-Age set)")
        else:
            print(f"   Expires: Session cookie")
    else:
        print("❌ Could not inspect cookie object")
    
    # Test 4: Logout and verify cookie is cleared
    print("\n[TEST 4] Logout - Verify Cookie is Cleared")
    print("-" * 80)
    
    response = session.post(f"{API_BASE}/auth/logout")
    
    if response.status_code == 200:
        print(f"✅ Logout successful: {response.status_code}")
        print(f"   Message: {response.json()['message']}")
    else:
        print(f"❌ Logout failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Test 5: Verify access is denied after logout
    print("\n[TEST 5] Verify Access Denied After Logout")
    print("-" * 80)
    
    response = session.get(f"{API_BASE}/auth/me")
    
    if response.status_code == 401:
        print(f"✅ Access correctly denied: {response.status_code}")
        print(f"   Error: {response.json().get('detail', 'No detail')}")
    else:
        print(f"❌ Expected 401, got: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Test 6: Backward compatibility - Test with Authorization header
    print("\n[TEST 6] Backward Compatibility - Authorization Header Still Works")
    print("-" * 80)
    
    # Login again to get a fresh token
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()['access_token']
        
        # Create a new session without cookies
        header_session = requests.Session()
        header_session.headers['Authorization'] = f"Bearer {token}"
        
        response = header_session.get(f"{API_BASE}/auth/me")
        if response.status_code == 200:
            print(f"✅ Authorization header still works: {response.status_code}")
            print(f"   User: {response.json()['username']}")
        else:
            print(f"⚠️ Authorization header not working: {response.status_code}")
            print(f"   This is expected if header support was removed")
    
    print("\n" + "=" * 80)
    print("🎉 COOKIE-BASED AUTHENTICATION TESTS COMPLETED")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        success = test_cookie_auth()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
