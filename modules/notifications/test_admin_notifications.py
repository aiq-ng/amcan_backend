"""
Test file to demonstrate admin notification management
This file shows how to use the new admin notification endpoints with filters and pagination
"""

import asyncio
import aiohttp
import json

# Example usage of the admin notification endpoints
async def test_admin_notification_management():
    """
    Example of how to use the admin notification endpoints:
    1. Get all notifications with pagination
    2. Filter notifications by various criteria
    3. Sort and search notifications
    """
    
    base_url = "http://localhost:8000"
    admin_token = "your_admin_token_here"  # Replace with actual admin token
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Get all notifications (first page)
        print("=== Test 1: Get all notifications (first page) ===")
        async with session.get(f"{base_url}/notifications/admin/all", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Total notifications: {data['total_count']}")
                print(f"Current page: {data['current_page']} of {data['total_pages']}")
                print(f"Notifications on this page: {len(data['notifications'])}")
                print(f"Has next page: {data['has_next']}")
                print(f"Has previous page: {data['has_previous']}")
                
                # Show first notification details
                if data['notifications']:
                    first_notif = data['notifications'][0]
                    print(f"First notification: {first_notif['notification_type']} - {first_notif['status']} - {first_notif['user_email']}")
            else:
                print(f"Failed to get notifications: {response.status}")
        
        # Test 2: Filter by status
        print("\n=== Test 2: Filter by status (unread) ===")
        async with session.get(f"{base_url}/notifications/admin/all?status=unread", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Unread notifications: {data['total_count']}")
                for notif in data['notifications'][:3]:  # Show first 3
                    print(f"- {notif['user_email']}: {notif['title']} ({notif['status']})")
            else:
                print(f"Failed to filter by status: {response.status}")
        
        # Test 3: Filter by notification type
        print("\n=== Test 3: Filter by notification type (system) ===")
        async with session.get(f"{base_url}/notifications/admin/all?notification_type=system", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"System notifications: {data['total_count']}")
                for notif in data['notifications'][:3]:  # Show first 3
                    print(f"- {notif['user_email']}: {notif['title']} ({notif['notification_type']})")
            else:
                print(f"Failed to filter by type: {response.status}")
        
        # Test 4: Filter by priority
        print("\n=== Test 4: Filter by priority (high) ===")
        async with session.get(f"{base_url}/notifications/admin/all?priority=high", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"High priority notifications: {data['total_count']}")
                for notif in data['notifications'][:3]:  # Show first 3
                    print(f"- {notif['user_email']}: {notif['title']} (Priority: {notif['priority']})")
            else:
                print(f"Failed to filter by priority: {response.status}")
        
        # Test 5: Search by user (email, name, or full name)
        print("\n=== Test 5: Search by user (email, name, or full name) ===")
        
        # Search by email
        print("--- Search by email ---")
        async with session.get(f"{base_url}/notifications/admin/all?user_search=patient", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Notifications with 'patient' in email/name: {data['total_count']}")
                for notif in data['notifications'][:3]:  # Show first 3
                    print(f"- {notif['user_email']} ({notif['first_name']} {notif['last_name']}): {notif['title']}")
            else:
                print(f"Failed to search by user: {response.status}")
        
        # Search by first name
        print("\n--- Search by first name ---")
        async with session.get(f"{base_url}/notifications/admin/all?user_search=John", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Notifications with 'John' in name/email: {data['total_count']}")
                for notif in data['notifications'][:3]:  # Show first 3
                    print(f"- {notif['user_email']} ({notif['first_name']} {notif['last_name']}): {notif['title']}")
            else:
                print(f"Failed to search by first name: {response.status}")
        
        # Search by last name
        print("\n--- Search by last name ---")
        async with session.get(f"{base_url}/notifications/admin/all?user_search=Doe", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Notifications with 'Doe' in name/email: {data['total_count']}")
                for notif in data['notifications'][:3]:  # Show first 3
                    print(f"- {notif['user_email']} ({notif['first_name']} {notif['last_name']}): {notif['title']}")
            else:
                print(f"Failed to search by last name: {response.status}")
        
        # Search by full name
        print("\n--- Search by full name ---")
        async with session.get(f"{base_url}/notifications/admin/all?user_search=John Doe", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Notifications with 'John Doe' in name/email: {data['total_count']}")
                for notif in data['notifications'][:3]:  # Show first 3
                    print(f"- {notif['user_email']} ({notif['first_name']} {notif['last_name']}): {notif['title']}")
            else:
                print(f"Failed to search by full name: {response.status}")
        
        # Test 6: Filter by date range
        print("\n=== Test 6: Filter by creation date range ===")
        from datetime import datetime, timedelta
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        params = {
            "created_at_from": week_ago.strftime("%Y-%m-%d"),
            "created_at_to": today.strftime("%Y-%m-%d")
        }
        
        async with session.get(f"{base_url}/notifications/admin/all", params=params, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Notifications created in last 7 days: {data['total_count']}")
                for notif in data['notifications'][:3]:  # Show first 3
                    print(f"- {notif['user_email']}: {notif['title']} (created: {notif['created_at']})")
            else:
                print(f"Failed to filter by date: {response.status}")
        
        # Test 7: Sort by different fields
        print("\n=== Test 7: Sort by priority (descending) ===")
        async with session.get(f"{base_url}/notifications/admin/all?sort_by=priority&sort_order=desc", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Notifications sorted by priority (desc): {data['total_count']}")
                for notif in data['notifications'][:5]:  # Show first 5
                    print(f"- {notif['priority']}: {notif['title']} ({notif['user_email']})")
            else:
                print(f"Failed to sort: {response.status}")
        
        # Test 8: Pagination
        print("\n=== Test 8: Pagination (page 2, 5 items per page) ===")
        async with session.get(f"{base_url}/notifications/admin/all?page=2&page_size=5", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Page 2 results: {len(data['notifications'])} items")
                print(f"Total pages: {data['total_pages']}")
                print(f"Has next: {data['has_next']}")
                print(f"Has previous: {data['has_previous']}")
                for notif in data['notifications']:
                    print(f"- {notif['user_email']}: {notif['title']}")
            else:
                print(f"Failed to paginate: {response.status}")
        
        # Test 9: Complex filter combination
        print("\n=== Test 9: Complex filter combination ===")
        params = {
            "status": "unread",
            "notification_type": "appointment",
            "priority": "high",
            "sort_by": "created_at",
            "sort_order": "desc",
            "page_size": "10"
        }
        
        async with session.get(f"{base_url}/notifications/admin/all", params=params, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                print(f"Unread high-priority appointment notifications: {data['total_count']}")
                for notif in data['notifications'][:3]:  # Show first 3
                    print(f"- {notif['user_email']}: {notif['title']} (Priority: {notif['priority']})")
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
        async with session.get(f"{base_url}/notifications/admin/all?created_at_from=invalid-date", headers=headers) as response:
            if response.status == 400:
                error_data = await response.json()
                print(f"Expected error for invalid date: {error_data}")
            else:
                print(f"Unexpected response: {response.status}")
        
        # Test invalid page number
        print("\n=== Test Error Handling: Invalid page number ===")
        async with session.get(f"{base_url}/notifications/admin/all?page=0", headers=headers) as response:
            if response.status == 422:
                error_data = await response.json()
                print(f"Expected validation error: {error_data}")
            else:
                print(f"Unexpected response: {response.status}")

if __name__ == "__main__":
    print("Testing admin notification management...")
    asyncio.run(test_admin_notification_management())
    
    print("\nTesting error handling...")
    asyncio.run(test_error_handling())
