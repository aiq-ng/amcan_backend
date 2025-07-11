# shared/schema.py
from shared.db import db

async def create_tables():
    async with db.get_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                is_admin BOOLEAN DEFAULT FALSE,
                is_doctor BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS doctors (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                title VARCHAR(100),
                bio TEXT,
                experience_years INTEGER,
                patients_count INTEGER,
                location VARCHAR(100),
                rating DECIMAL(3,1) DEFAULT 0.0,
                availability JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                doctor_id INTEGER REFERENCES doctors(id),
                user_id INTEGER REFERENCES users(id),
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                doctor_id INTEGER REFERENCES doctors(id),
                user_id INTEGER REFERENCES users(id),
                slot_time TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                appointment_id INTEGER REFERENCES appointments(id),
                sender_id INTEGER REFERENCES users(id),
                receiver_id INTEGER REFERENCES users(id),
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (sender_id != receiver_id)
            );

            CREATE TABLE IF NOT EXISTS feed_items (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('video', 'audio', 'article')),
                url VARCHAR(255),
                content TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES users(id)
            );
                           
            CREATE TABLE IF NOT EXISTS video_calls (
                id SERIAL PRIMARY KEY,
                appointment_id INTEGER REFERENCES appointments(id),
                initiator_id INTEGER REFERENCES users(id),
                receiver_id INTEGER REFERENCES users(id),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status VARCHAR(20) DEFAULT 'initiated' CHECK (status IN ('initiated', 'active', 'ended')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS products (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price INT NOT NULL, -- Stored in smallest currency unit (e.g., kobo for NGN)
                currency VARCHAR(3) DEFAULT 'NGN',
                image_urls TEXT[], -- Array of text for multiple image URLs
                average_rating NUMERIC(2, 1) DEFAULT 0.0,
                total_reviews INT DEFAULT 0,
                category_id VARCHAR(255),
                is_high_demand BOOLEAN DEFAULT FALSE,
                -- Consider adding specific fields for key_benefits and specifications if they are simple text fields,
                -- or manage them via separate join tables for more complex structures.
                -- For this request, assume key_benefits and specifications are stored as JSONB or text arrays within the products table itself for simplicity, if needed.
                key_benefits TEXT[],
                specifications JSONB -- Example: [{"name": "Weight", "value": "12 lbs"}]
            );

            CREATE TABLE IF NOT EXISTS categories (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id VARCHAR(255) PRIMARY KEY,
                product_id VARCHAR(255) NOT NULL REFERENCES products(id),
                user_id INT NOT NULL, -- Placeholder for actual user system
                rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """)