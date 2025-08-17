"""
Test file to demonstrate admin subscription management
This file shows how to use the new admin subscription endpoints with filters and pagination
"""

import asyncio
import aiohttp
import json

# Example usage of the admin subscription endpoints
async def test_admin_subscription_management():
    """
    Example of how to use the admin subscription endpoints:
    1. Get all subscriptions with pagination
    2. Filter subscriptions by various criteria
    3. Sort and search subscriptions
    """
    
    base_url = "http://localhost:8000"
    admin_token = "your_admin_token_here"  # Replace with actual admin token
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Get all subscriptions (first page)
        print("=== Test 1: Get all subscriptions (first page) ===")
        async with session.get(f"{base_url}/subscriptions/admin/all", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Total subscriptions: {data['total_count']}")
                print(f"Current page: {data['current_page']} of {data['total_pages']}")
                print(f"Subscriptions on this page: {len(data['subscriptions'])}")
                print(f"Has next page: {data['has_next']}")
                print(f"Has previous page: {data['has_previous']}")
                
                # Show first subscription details
                if data['subscriptions']:
                    first_sub = data['subscriptions'][0]
                    print(f"First subscription: {first_sub['subscription_type']} - {first_sub['status']} - {first_sub['user_email']}")
            else:
                print(f"Failed to get subscriptions: {response.status}")
        
        # Test 2: Filter by status
        print("\n=== Test 2: Filter by status (active) ===")
        async with session.get(f"{base_url}/subscriptions/admin/all?status=active", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Active subscriptions: {data['total_count']}")
                for sub in data['subscriptions'][:3]:  # Show first 3
                    print(f"- {sub['user_email']}: {sub['subscription_type']} ({sub['status']})")
            else:
                print(f"Failed to filter by status: {response.status}")
        
        # Test 3: Filter by subscription type
        print("\n=== Test 3: Filter by subscription type (premium) ===")
        async with session.get(f"{base_url}/subscriptions/admin/all?subscription_type=premium", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Premium subscriptions: {data['total_count']}")
                for sub in data['subscriptions'][:3]:  # Show first 3
                    print(f"- {sub['user_email']}: {sub['subscription_type']} ({sub['status']})")
            else:
                print(f"Failed to filter by type: {response.status}")
        
        # Test 3.5: Filter by subscription plan ID
        print("\n=== Test 3.5: Filter by subscription plan ID ===")
        async with session.get(f"{base_url}/subscriptions/admin/all?plan_id=1", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Subscriptions with plan ID 1: {data['total_count']}")
                for sub in data['subscriptions'][:3]:  # Show first 3
                    print(f"- {sub['user_email']}: {sub['subscription_type']} (Plan: {sub.get('plan_name', 'N/A')} - {sub.get('plan_price', 'N/A')} {sub.get('plan_currency', 'N/A')})")
            else:
                print(f"Failed to filter by plan ID: {response.status}")
        
        # Test 4: Search by user (email, name, or full name)
        print("\n=== Test 4: Search by user (email, name, or full name) ===")
        
        # Search by email
        print("--- Search by email ---")
        async with session.get(f"{base_url}/subscriptions/admin/all?user_search=patient", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Subscriptions with 'patient' in email/name: {data['total_count']}")
                for sub in data['subscriptions'][:3]:  # Show first 3
                    print(f"- {sub['user_email']} ({sub['first_name']} {sub['last_name']}): {sub['subscription_type']} ({sub['status']})")
            else:
                print(f"Failed to search by user: {response.status}")
        
        # Search by first name
        print("\n--- Search by first name ---")
        async with session.get(f"{base_url}/subscriptions/admin/all?user_search=John", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Subscriptions with 'John' in name/email: {data['total_count']}")
                for sub in data['subscriptions'][:3]:  # Show first 3
                    print(f"- {sub['user_email']} ({sub['first_name']} {sub['last_name']}): {sub['subscription_type']} ({sub['status']})")
            else:
                print(f"Failed to search by first name: {response.status}")
        
        # Search by last name
        print("\n--- Search by last name ---")
        async with session.get(f"{base_url}/subscriptions/admin/all?user_search=Doe", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Subscriptions with 'Doe' in name/email: {data['total_count']}")
                for sub in data['subscriptions'][:3]:  # Show first 3
                    print(f"- {sub['user_email']} ({sub['first_name']} {sub['last_name']}): {sub['subscription_type']} ({sub['status']})")
            else:
                print(f"Failed to search by last name: {response.status}")
        
        # Search by full name
        print("\n--- Search by full name ---")
        async with session.get(f"{base_url}/subscriptions/admin/all?user_search=John Doe", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Subscriptions with 'John Doe' in name/email: {data['total_count']}")
                for sub in data['subscriptions'][:3]:  # Show first 3
                    print(f"- {sub['user_email']} ({sub['first_name']} {sub['last_name']}): {sub['subscription_type']} ({sub['status']})")
            else:
                print(f"Failed to search by full name: {response.status}")
        
        # Test 5: Filter by date range
        print("\n=== Test 5: Filter by date range ===")
        from datetime import datetime, timedelta
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        params = {
            "start_date_from": week_ago.strftime("%Y-%m-%d"),
            "start_date_to": today.strftime("%Y-%m-%d")
        }
        
        async with session.get(f"{base_url}/subscriptions/admin/all", params=params, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Subscriptions started in last 7 days: {data['total_count']}")
                for sub in data['subscriptions'][:3]:  # Show first 3
                    print(f"- {sub['user_email']}: {sub['subscription_type']} (started: {sub['start_date']})")
            else:
                print(f"Failed to filter by date: {response.status}")
        
        # Test 6: Sort by different fields
        print("\n=== Test 6: Sort by subscription type (ascending) ===")
        async with session.get(f"{base_url}/subscriptions/admin/all?sort_by=subscription_type&sort_order=asc", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Subscriptions sorted by type (asc): {data['total_count']}")
                for sub in data['subscriptions'][:5]:  # Show first 5
                    print(f"- {sub['subscription_type']}: {sub['user_email']}")
            else:
                print(f"Failed to sort: {response.status}")
        
        # Test 7: Pagination
        print("\n=== Test 7: Pagination (page 2, 5 items per page) ===")
        async with session.get(f"{base_url}/subscriptions/admin/all?page=2&page_size=5", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Page 2 results: {len(data['subscriptions'])} items")
                print(f"Total pages: {data['total_pages']}")
                print(f"Has next: {data['has_next']}")
                print(f"Has previous: {data['has_previous']}")
                for sub in data['subscriptions']:
                    print(f"- {sub['user_email']}: {sub['subscription_type']}")
            else:
                print(f"Failed to paginate: {response.status}")
        
        # Test 8: Complex filter combination
        print("\n=== Test 8: Complex filter combination ===")
        params = {
            "status": "active",
            "subscription_type": "premium",
            "auto_renew": "true",
            "sort_by": "created_at",
            "sort_order": "desc",
            "page_size": "10"
        }
        
        async with session.get(f"{base_url}/subscriptions/admin/all", params=params, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Active premium subscriptions with auto-renew: {data['total_count']}")
                for sub in data['subscriptions'][:3]:  # Show first 3
                    print(f"- {sub['user_email']}: {sub['subscription_type']} (auto-renew: {sub['auto_renew']})")
            else:
                print(f"Failed complex filter: {response.status}")

# Example of error handling
async def test_error_handling():
    """Test error handling for invalid parameters"""
    
    base_url = "http://localhost:8000"
    admin_token = "your_admin_token_here"  # Replace with actual admin token
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with aiohttp.ClientSession() as session:
        # Test invalid date format
        print("\n=== Test Error Handling: Invalid date format ===")
        async with session.get(f"{base_url}/subscriptions/admin/all?start_date_from=invalid-date", headers=headers) as response:
            if response.status == 400:
                error_data = await response.json()
                print(f"Expected error for invalid date: {error_data}")
            else:
                print(f"Unexpected response: {response.status}")
        
        # Test invalid page number
        print("\n=== Test Error Handling: Invalid page number ===")
        async with session.get(f"{base_url}/subscriptions/admin/all?page=0", headers=headers) as response:
            if response.status == 422:
                error_data = await response.json()
                print(f"Expected validation error: {error_data}")
            else:
                print(f"Unexpected response: {response.status}")

if __name__ == "__main__":
    print("Testing admin subscription management...")
    asyncio.run(test_admin_subscription_management())
    
    print("\nTesting error handling...")
    asyncio.run(test_error_handling())
