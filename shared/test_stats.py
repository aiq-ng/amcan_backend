"""
Test file to demonstrate general statistics endpoints
This file shows how to use the statistics endpoints for platform analytics
"""

import asyncio
import aiohttp
import json

# Example usage of the statistics endpoints
async def test_general_stats():
    """
    Example of how to use the statistics endpoints:
    1. Get comprehensive platform statistics
    2. Get dashboard statistics
    3. Get revenue analytics
    """
    
    base_url = "http://localhost:8000"
    admin_token = "your_admin_token_here"  # Replace with actual admin token
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Get comprehensive platform statistics
        print("=== Test 1: Get comprehensive platform statistics ===")
        async with session.get(f"{base_url}/stats/platform", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                
                print("📊 Platform Statistics:")
                print(f"  Total Patients: {data['basic_counts']['total_patients']}")
                print(f"  Total Doctors: {data['basic_counts']['total_doctors']}")
                print(f"  Subscribed Patients: {data['basic_counts']['total_subscribed_patients']}")
                print(f"  Video Call Sessions: {data['basic_counts']['total_video_call_sessions']}")
                print(f"  Active Subscriptions: {data['basic_counts']['active_subscriptions']}")
                
                print(f"\n💰 Financial Summary:")
                print(f"  Total Revenue (Current Year): {data['financial_summary']['total_revenue_current_year']} {data['financial_summary']['currency']}")
                
                print(f"\n📈 Growth Metrics (This Month):")
                print(f"  New Patients: {data['growth_metrics']['new_patients_this_month']}")
                print(f"  New Doctors: {data['growth_metrics']['new_doctors_this_month']}")
                print(f"  Video Calls: {data['growth_metrics']['video_calls_this_month']}")
                
                print(f"\n🏆 Top 5 Doctors by Video Calls:")
                for i, doctor in enumerate(data['top_doctors'], 1):
                    print(f"  {i}. {doctor['name']} ({doctor['title']}) - {doctor['video_call_count']} calls (Rating: {doctor['rating']})")
                
                print(f"\n🔔 Recent Notifications:")
                for i, notification in enumerate(data['recent_notifications'], 1):
                    print(f"  {i}. {notification['title']} - {notification['user_name']} ({notification['notification_type']})")
                
                print(f"\n📅 Monthly Revenue Breakdown:")
                for revenue in data['monthly_revenue']:
                    print(f"  {revenue['month']}: {revenue['total_revenue']} {revenue['currency']} ({revenue['subscription_count']} subscriptions)")
                    
            else:
                print(f"Failed to get platform stats: {response.status}")
        
        # Test 2: Get dashboard statistics
        print("\n=== Test 2: Get dashboard statistics ===")
        async with session.get(f"{base_url}/stats/dashboard", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                
                print("📊 Dashboard Overview:")
                print(f"  Total Patients: {data['overview']['total_patients']}")
                print(f"  Total Doctors: {data['overview']['total_doctors']}")
                print(f"  Active Subscriptions: {data['overview']['active_subscriptions']}")
                print(f"  Total Video Calls: {data['overview']['total_video_calls']}")
                
                print(f"\n📅 Today's Activity:")
                print(f"  New Patients: {data['today']['new_patients']}")
                print(f"  New Doctors: {data['today']['new_doctors']}")
                print(f"  Video Calls: {data['today']['video_calls']}")
                
                print(f"\n💰 This Month's Revenue:")
                print(f"  Revenue: {data['this_month']['revenue']} {data['this_month']['currency']}")
                
            else:
                print(f"Failed to get dashboard stats: {response.status}")
        
        # Test 3: Get revenue analytics for current year
        print("\n=== Test 3: Get revenue analytics (current year) ===")
        async with session.get(f"{base_url}/stats/revenue", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                
                print(f"💰 Revenue Analytics for {data['year']}:")
                print(f"  Total Revenue: {data['total_revenue']} {data['currency']}")
                
                print(f"\n📅 Monthly Breakdown:")
                for month_data in data['monthly_breakdown']:
                    print(f"  {month_data['month']}: {month_data['revenue']} {month_data['currency']} ({month_data['subscription_count']} subscriptions)")
                
                print(f"\n📋 Plan-wise Breakdown:")
                for plan_data in data['plan_breakdown']:
                    print(f"  {plan_data['plan_type']}: {plan_data['revenue']} {plan_data['currency']} ({plan_data['subscription_count']} subscriptions)")
                
            else:
                print(f"Failed to get revenue analytics: {response.status}")
        
        # Test 4: Get revenue analytics for specific year
        print("\n=== Test 4: Get revenue analytics (2023) ===")
        async with session.get(f"{base_url}/stats/revenue?year=2023", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                
                print(f"💰 Revenue Analytics for {data['year']}:")
                print(f"  Total Revenue: {data['total_revenue']} {data['currency']}")
                
                print(f"\n📅 Monthly Breakdown:")
                for month_data in data['monthly_breakdown']:
                    print(f"  {month_data['month']}: {month_data['revenue']} {month_data['currency']} ({month_data['subscription_count']} subscriptions)")
                
            else:
                print(f"Failed to get revenue analytics for 2023: {response.status}")

# Example of error handling
async def test_error_handling():
    """Test error handling for invalid requests"""
    
    base_url = "http://localhost:8000"
    admin_token = "your_admin_token_here"  # Replace with actual admin token
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with aiohttp.ClientSession() as session:
        # Test unauthorized access
        print("\n=== Test Error Handling: Unauthorized Access ===")
        async with session.get(f"{base_url}/stats/platform") as response:  # No auth header
            if response.status == 401:
                error_data = await response.json()
                print(f"Expected unauthorized error: {error_data}")
            else:
                print(f"Unexpected response: {response.status}")
        
        # Test invalid year parameter
        print("\n=== Test Error Handling: Invalid Year ===")
        async with session.get(f"{base_url}/stats/revenue?year=invalid", headers=headers) as response:
            if response.status == 422:
                error_data = await response.json()
                print(f"Expected validation error: {error_data}")
            else:
                print(f"Unexpected response: {response.status}")

if __name__ == "__main__":
    print("Testing general statistics endpoints...")
    asyncio.run(test_general_stats())
    
    print("\nTesting error handling...")
    asyncio.run(test_error_handling())
