"""
Test file to demonstrate refresh token functionality
This file shows how to use the new refresh token endpoints
"""

import asyncio
import aiohttp
import json

# Example usage of the refresh token flow
async def test_refresh_token_flow():
    """
    Example of how to use the refresh token flow:
    1. Login to get access_token and refresh_token
    2. Use access_token for API calls
    3. When access_token expires, use refresh_token to get new tokens
    """
    
    base_url = "http://localhost:8000/auth"
    
    # Step 1: Login to get tokens
    login_data = {
        "username": "user@example.com",  # email
        "password": "password123"
    }
    
    async with aiohttp.ClientSession() as session:
        # Login
        async with session.post(f"{base_url}/login", data=login_data) as response:
            if response.status == 200:
                login_result = await response.json()
                tokens = login_result["data"]
                
                access_token = tokens["access_token"]
                refresh_token = tokens["refresh_token"]
                
                print("Login successful!")
                print(f"Access token: {access_token[:50]}...")
                print(f"Refresh token: {refresh_token[:50]}...")
                
                # Step 2: Use access token for API calls
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Example API call
                async with session.get(f"{base_url}/me", headers=headers) as me_response:
                    if me_response.status == 200:
                        user_data = await me_response.json()
                        print(f"User data: {user_data}")
                    else:
                        print(f"Failed to get user data: {me_response.status}")
                
                # Step 3: When access token expires, use refresh token
                refresh_data = {
                    "refresh_token": refresh_token
                }
                
                async with session.post(f"{base_url}/refresh", json=refresh_data) as refresh_response:
                    if refresh_response.status == 200:
                        refresh_result = await refresh_response.json()
                        new_tokens = refresh_result["data"]
                        
                        new_access_token = new_tokens["access_token"]
                        new_refresh_token = new_tokens["refresh_token"]
                        
                        print("Token refresh successful!")
                        print(f"New access token: {new_access_token[:50]}...")
                        print(f"New refresh token: {new_refresh_token[:50]}...")
                        
                        # Use new access token for subsequent API calls
                        new_headers = {"Authorization": f"Bearer {new_access_token}"}
                        
                        async with session.get(f"{base_url}/me", headers=new_headers) as new_me_response:
                            if new_me_response.status == 200:
                                new_user_data = await new_me_response.json()
                                print(f"User data with new token: {new_user_data}")
                            else:
                                print(f"Failed to get user data with new token: {new_me_response.status}")
                    else:
                        print(f"Failed to refresh token: {refresh_response.status}")
            else:
                print(f"Login failed: {response.status}")

# Example of error handling
async def test_invalid_refresh_token():
    """Test what happens with an invalid refresh token"""
    
    base_url = "http://localhost:8000/auth"
    
    invalid_refresh_data = {
        "refresh_token": "invalid_token_here"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base_url}/refresh", json=invalid_refresh_data) as response:
            if response.status == 401:
                error_data = await response.json()
                print(f"Expected error for invalid token: {error_data}")
            else:
                print(f"Unexpected response: {response.status}")

if __name__ == "__main__":
    print("Testing refresh token flow...")
    asyncio.run(test_refresh_token_flow())
    
    print("\nTesting invalid refresh token...")
    asyncio.run(test_invalid_refresh_token())
