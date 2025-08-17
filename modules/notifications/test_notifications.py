# """
# Test file to demonstrate notifications functionality
# This file shows how to use the notification endpoints and WebSocket
# """

# import asyncio
# import aiohttp
# import json
# import websockets

# # Example usage of the notifications flow
# async def test_notifications_flow():
#     """
#     Example of how to use the notification endpoints:
#     1. Create a notification
#     2. Get user's notifications
#     3. Mark notification as read
#     4. Send bulk notifications
#     """
    
#     base_url = "http://localhost:8000"
#     admin_token = "your_admin_token_here"  # Replace with actual admin token
#     user_token = "your_user_token_here"    # Replace with actual user token
    
#     admin_headers = {"Authorization": f"Bearer {admin_token}"}
#     user_headers = {"Authorization": f"Bearer {user_token}"}
    
#     async with aiohttp.ClientSession() as session:
#         # Step 1: Create a notification (Admin only)
#         notification_data = {
#             "user_id": 1,
#             "title": "Welcome to our platform!",
#             "message": "Thank you for joining us. We're excited to have you on board.",
#             "notification_type": "system",
#             "priority": "medium"
#         }
        
#         async with session.post(f"{base_url}/notifications/", json=notification_data, headers=admin_headers) as response:
#             if response.status == 200:
#                 result = await response.json()
#                 notification = result["data"]
#                 print(f"Notification created: {notification}")
                
#                 notification_id = notification["id"]
                
#                 # Step 2: Get user's notifications
#                 async with session.get(f"{base_url}/notifications/", headers=user_headers) as get_response:
#                     if get_response.status == 200:
#                         get_result = await get_response.json()
#                         notifications = get_result["data"]
#                         print(f"User notifications: {notifications}")
                
#                 # Step 3: Get unread count
#                 async with session.get(f"{base_url}/notifications/unread-count", headers=user_headers) as count_response:
#                     if count_response.status == 200:
#                         count_result = await count_response.json()
#                         unread_count = count_result["data"]["unread_count"]
#                         print(f"Unread notifications: {unread_count}")
                
#                 # Step 4: Mark notification as read
#                 async with session.put(f"{base_url}/notifications/{notification_id}/read", headers=user_headers) as read_response:
#                     if read_response.status == 200:
#                         read_result = await read_response.json()
#                         print(f"Notification marked as read: {read_result}")
                
#                 # Step 5: Send bulk notification (Admin only)
#                 bulk_data = {
#                     "user_ids": [1, 2, 3],
#                     "title": "System Maintenance",
#                     "message": "We will be performing system maintenance tonight at 2 AM.",
#                     "notification_type": "system",
#                     "priority": "high"
#                 }
                
#                 async with session.post(f"{base_url}/notifications/bulk", json=bulk_data, headers=admin_headers) as bulk_response:
#                     if bulk_response.status == 200:
#                         bulk_result = await bulk_response.json()
#                         print(f"Bulk notification sent: {bulk_result}")
#             else:
#                 print(f"Failed to create notification: {response.status}")

# # Example WebSocket usage
# async def test_websocket_notifications():
#     """
#     Example of how to use WebSocket for real-time notifications
#     """
#     token = "your_user_token_here"  # Replace with actual user token
#     uri = f"ws://localhost:8000/notifications/ws?token={token}"
    
#     try:
#         async with websockets.connect(uri) as websocket:
#             print("Connected to WebSocket")
            
#             # Subscribe to system notifications
#             subscribe_message = {
#                 "type": "subscribe",
#                 "notification_type": "system"
#             }
#             await websocket.send(json.dumps(subscribe_message))
            
#             # Listen for notifications
#             async for message in websocket:
#                 data = json.loads(message)
#                 print(f"Received notification: {data}")
                
#                 # Handle different message types
#                 if data.get("type") == "notification":
#                     notification = data.get("data")
#                     print(f"New notification: {notification['title']} - {notification['message']}")
#                 elif data.get("type") == "subscribed":
#                     print(f"Subscribed to: {data.get('notification_type')}")
#                 elif data.get("type") == "pong":
#                     print("Received pong")
                    
#     except Exception as e:
#         print(f"WebSocket error: {e}")

# if __name__ == "__main__":
#     print("Testing notifications flow...")
#     asyncio.run(test_notifications_flow())
    
#     print("\nTesting WebSocket notifications...")
#     asyncio.run(test_websocket_notifications())
