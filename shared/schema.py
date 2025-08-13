# shared/schema.py
from shared.db import db

async def create_tables():
    async with db.get_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                is_doctor BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
                           
            CREATE TABLE IF NOT EXISTS therapy (
                id SERIAL PRIMARY KEY,
                therapy_type VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                date_of_birth DATE,
                address VARCHAR(255),
                profile_image_url VARCHAR(255), -- URL to the patient's profile image
                phone_number VARCHAR(20),
                occupation VARCHAR(100),
                therapy_type INTEGER REFERENCES therapy(id),
                therapy_criticality VARCHAR(50) CHECK (therapy_criticality IN ('High', 'Medium', 'Low')),
                emergency_contact_name VARCHAR(100),
                emergency_contact_phone VARCHAR(20),
                marital_status VARCHAR(20) CHECK (marital_status IN ('Single', 'Married', 'Divorced', 'Widowed')),
                account_type VARCHAR(20) DEFAULT 'unsubscribed' CHECK (account_type IN ('subscribed', 'unsubscribed')),
                session_count INTEGER DEFAULT 0,
                account_status VARCHAR(20) DEFAULT 'active' CHECK (account_status IN ('active', 'inactive', 'new patient')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS subscription (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patients(id),
                plan_name VARCHAR(100) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                status VARCHAR(20) CHECK (status IN ('active', 'inactive', 'cancelled')) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS doctors (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                title VARCHAR(100),
                bio TEXT,
                experience_years INTEGER,
                patients_count INTEGER,
                location VARCHAR(100),
                rating DECIMAL(3,1) DEFAULT 0.0,
                profile_picture_url VARCHAR(255), -- URL to the doctor's profile picture
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
                           
            CREATE TABLE IF NOT EXISTS doctor_availability_slots (
                id SERIAL PRIMARY KEY,
                doctor_id INTEGER REFERENCES doctors(id) ON DELETE CASCADE,
                available_at TIMESTAMP WITH TIME ZONE NOT NULL,             -- exact date & time, now correctly defined with timezone
                status VARCHAR(20) DEFAULT 'available',                 -- 'available', 'booked', 'expired'
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Changed to TIMESTAMP WITH TIME ZONE for consistency

                UNIQUE (doctor_id, available_at)                        -- prevent duplicate time slots per doctor
            );

            CREATE TABLE IF NOT EXISTS doctors_experience (
                id SERIAL PRIMARY KEY,
                doctor_id INTEGER REFERENCES doctors(id),
                institution VARCHAR(255) NOT NULL,
                position VARCHAR(255) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS doctors_reviews (
                id SERIAL PRIMARY KEY,
                doctor_id INTEGER REFERENCES doctors(id),
                user_id INTEGER REFERENCES users(id),
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS doctors_patients (
                id SERIAL PRIMARY KEY,
                doctor_id INTEGER REFERENCES doctors(id),
                patient_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                doctor_id INTEGER REFERENCES doctors(id) ON DELETE CASCADE,
                patient_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                slot_time TIMESTAMP,
                complain VARCHAR(255),
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS appointments_summary (
                id SERIAL PRIMARY KEY,
                doctor_id INTEGER REFERENCES doctors(id),
                patient_id INTEGER REFERENCES users(id),
                diagnosis TEXT,
                notes TEXT,
                prescription TEXT,
                follow_up_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price INT NOT NULL, -- Stored in smallest currency unit (e.g., kobo for NGN)
                currency VARCHAR(3) DEFAULT 'NGN',
                image_urls TEXT[], -- Array of text for multiple image URLs
                average_rating NUMERIC(2, 1) DEFAULT 0.0,
                total_reviews INT DEFAULT 0,
                category_id INTEGER,
                is_high_demand BOOLEAN DEFAULT FALSE,
                -- Consider adding specific fields for key_benefits and specifications if they are simple text fields,
                -- or manage them via separate join tables for more complex structures.
                -- For this request, assume key_benefits and specifications are stored as JSONB or text arrays within the products table itself for simplicity, if needed.
                key_benefits TEXT[],
                specifications JSONB -- Example: [{"name": "Weight", "value": "12 lbs"}]
            );

            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS product_reviews (
                id VARCHAR(255) PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(id),
                user_id INTEGER NOT NULL, -- Placeholder for actual user system
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,           
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                category_id INTEGER REFERENCES categories(id), -- Assuming categories table exists
                description TEXT, -- Short summary or description of the blog post
                content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('video', 'audio', 'article')),
                content_url VARCHAR(255), -- For video/audio URLs from Cloudinary; article content stored here
                thumbnail_url VARCHAR(225),
                duration INT, -- In seconds for video/audio; NULL for articles
                mood_relevance JSONB, -- e.g., {"Happy": 0.8, "Calm": 0.5} for relevance scores
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS mood_recommendations (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) UNIQUE,
                current_mood VARCHAR(50) NOT NULL CHECK (current_mood IN ('Happy', 'Calm', 'Manic', 'Sad', 'Angry')),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            """)