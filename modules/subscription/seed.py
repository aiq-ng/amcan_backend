"""
Seed file for subscription plans
This file populates the subscription_plans table with default plans
"""

import asyncio
from shared.db import db

async def seed_subscription_plans():
    """Seed the subscription_plans table with default plans"""
    
    default_plans = [
        {
            "name": "Basic Plan",
            "type": "basic",
            "price": 9.99,
            "currency": "NGN",
            "duration_days": 30,
            "features": [
                "Basic consultation access",
                "Standard appointment booking",
                "Email support",
                "Basic health tracking"
            ],
            "is_active": True
        },
        {
            "name": "Premium Plan",
            "type": "premium",
            "price": 29.99,
            "currency": "NGN",
            "duration_days": 30,
            "features": [
                "All Basic features",
                "Priority consultation access",
                "Video call appointments",
                "24/7 support",
                "Advanced health tracking",
                "Prescription management",
                "Health reports"
            ],
            "is_active": True
        },
        {
            "name": "Enterprise Plan",
            "type": "enterprise",
            "price": 99.99,
            "currency": "NGN",
            "duration_days": 30,
            "features": [
                "All Premium features",
                "Dedicated health coach",
                "Family member management",
                "Custom health plans",
                "Priority scheduling",
                "Health analytics dashboard",
                "Integration with health devices",
                "Monthly health reports"
            ],
            "is_active": True
        }
    ]
    
    async with db.get_connection() as conn:
        for plan in default_plans:
            # Check if plan already exists
            existing = await conn.fetchrow(
                "SELECT id FROM subscription_plans WHERE type = $1",
                plan["type"]
            )
            
            if not existing:
                await conn.execute(
                    """
                    INSERT INTO subscription_plans (name, type, price, currency, duration_days, features, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    plan["name"],
                    plan["type"],
                    plan["price"],
                    plan["currency"],
                    plan["duration_days"],
                    plan["features"],
                    plan["is_active"]
                )
                print(f"Created subscription plan: {plan['name']}")
            else:
                print(f"Subscription plan already exists: {plan['name']}")

async def main():
    """Main function to run the seeding"""
    print("Seeding subscription plans...")
    await seed_subscription_plans()
    print("Subscription plans seeding completed!")

if __name__ == "__main__":
    asyncio.run(main())
