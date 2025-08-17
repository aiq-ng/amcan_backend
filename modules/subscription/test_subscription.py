# """
# Test file to demonstrate subscription functionality
# This file shows how to use the subscription endpoints
# """

# import asyncio
# import aiohttp
# import json

# # Example usage of the subscription flow
# async def test_subscription_flow():
#     """
#     Example of how to use the subscription endpoints:
#     1. Create a subscription for a user
#     2. Get user's subscription
#     3. Update subscription
#     4. Cancel subscription
#     """
    
#     base_url = "http://localhost:8000"
#     admin_token = "your_admin_token_here"  # Replace with actual admin token
    
#     headers = {"Authorization": f"Bearer {admin_token}"}
    
#     async with aiohttp.ClientSession() as session:
#         # Step 1: Create a subscription
#         subscription_data = {
#             "user_id": 1,
#             "subscription_type": "premium",
#             "auto_renew": True,
#             "payment_method": "credit_card"
#         }
        
#         async with session.post(f"{base_url}/subscriptions/", json=subscription_data, headers=headers) as response:
#             if response.status == 200:
#                 result = await response.json()
#                 subscription = result["data"]
#                 print(f"Subscription created: {subscription}")
                
#                 subscription_id = subscription["id"]
                
#                 # Step 2: Get available plans
#                 async with session.get(f"{base_url}/subscriptions/plans/available") as plans_response:
#                     if plans_response.status == 200:
#                         plans_result = await plans_response.json()
#                         plans = plans_result["data"]
#                         print(f"Available plans: {plans}")
                
#                 # Step 3: Update subscription
#                 update_data = {
#                     "auto_renew": False
#                 }
                
#                 async with session.put(f"{base_url}/subscriptions/{subscription_id}", json=update_data, headers=headers) as update_response:
#                     if update_response.status == 200:
#                         update_result = await update_response.json()
#                         print(f"Subscription updated: {update_result}")
                
#                 # Step 4: Cancel subscription
#                 async with session.delete(f"{base_url}/subscriptions/{subscription_id}", headers=headers) as cancel_response:
#                     if cancel_response.status == 200:
#                         cancel_result = await cancel_response.json()
#                         print(f"Subscription cancelled: {cancel_result}")
#             else:
#                 print(f"Failed to create subscription: {response.status}")

# if __name__ == "__main__":
#     print("Testing subscription flow...")
#     asyncio.run(test_subscription_flow())
