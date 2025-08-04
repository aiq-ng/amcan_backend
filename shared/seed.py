from shared.db import db
from modules.auth.utils import hash_password
from datetime import datetime, date, timedelta
import logging
from random import randint, choice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_data():
    async with db.get_connection() as conn:
        logger.info("Checking if users table is empty...")
        count = await conn.fetchval("SELECT COUNT(*) FROM users")
        if count == 0:
            logger.info("No users found. Seeding data...")

            # Seed therapy types
            logger.info("Seeding therapy types...")
            therapy_types = ["Psychotherapy", "Physical Therapy", "Occupational Therapy", "Speech Therapy"]
            therapy_ids = []
            for therapy_type in therapy_types:
                therapy_id = await conn.fetchval(
                    """
                    INSERT INTO therapy (therapy_type)
                    VALUES ($1)
                    RETURNING id
                    """,
                    therapy_type
                )
                therapy_ids.append(therapy_id)
                logger.info(f"Therapy type {therapy_type} created with id: {therapy_id}")

            # Seed admin user
            logger.info("Seeding admin user...")
            password_hash = hash_password("Admin123!")
            admin_id = await conn.fetchval(
                """
                INSERT INTO users (email, password_hash, is_admin)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                "admin@therapyapp.com", password_hash, True
            )
            logger.info(f"Admin user created with id: {admin_id}")

            # Seed multiple patients
            logger.info("Seeding patients...")
            patients = []
            patient_data = [
                ("patient1@therapyapp.com", "Patient123!", "Jane", "Doe", date(1990, 5, 15), '123 Main St, Kaduna', '+2348012345678', 'Teacher', therapy_ids[0], 'High', 'John Doe', '+2348098765432', 'Single'),
                ("patient2@therapyapp.com", "Patient456!", "Ali", "Bello", date(1985, 9, 22), '456 Lagos Rd, Lagos', '+2348076543210', 'Engineer', therapy_ids[1], 'Medium', 'Fatima Bello', '+2348081234567', 'Married'),
                ("patient3@therapyapp.com", "Patient789!", "Amina", "Sani", date(1995, 3, 10), '789 Kano St, Kano', '+2348065432109', 'Nurse', therapy_ids[2], 'Low', 'Hassan Sani', '+2348054321098', 'Single'),
                ("patient4@therapyapp.com", "Patient101!", "Chika", "Okonkwo", date(1988, 12, 5), '321 Enugu Ave, Enugu', '+2348043210987', 'Accountant', therapy_ids[3], 'Medium', 'Ngozi Okonkwo', '+2348032109876', 'Married'),
                ("patient5@therapyapp.com", "Patient112!", "Tunde", "Adewale", date(1992, 7, 18), '654 Ibadan Rd, Ibadan', '+2348021098765', 'Driver', therapy_ids[0], 'High', 'Bisi Adewale', '+2348010987654', 'Divorced'),
            ]
            for email, pwd, fname, lname, dob, addr, phone, occ, therapy_id, criticality, ec_name, ec_phone, ms in patient_data:
                patient_id = await conn.fetchval(
                    """
                    INSERT INTO users (email, password_hash)
                    VALUES ($1, $2)
                    RETURNING id
                    """,
                    email, hash_password(pwd)
                )
                await conn.execute(
                    """
                    INSERT INTO patients (user_id, first_name, last_name, date_of_birth, address, profile_image_url, phone_number, occupation, therapy_type, therapy_criticality, emergency_contact_name, emergency_contact_phone, marital_status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """,
                    patient_id, fname, lname, dob, addr, f'https://example.com/patient{patient_id}.jpg', phone, occ, therapy_id, criticality, ec_name, ec_phone, ms
                )
                patients.append(patient_id)
                logger.info(f"Patient {fname} {lname} created with id: {patient_id}")

            # Seed multiple doctors
            logger.info("Seeding doctors...")
            doctors = []
            doctor_data = [
                ("doctor1@therapyapp.com", "Doctor123!", "Abimbola", "Taofeek", "Psychologist", 6, 120, "Kaduna", "https://example.com/doctor1.jpg"),
                ("doctor2@therapyapp.com", "Doctor456!", "Aisha", "Mohammed", "Therapist", 8, 150, "Lagos", "https://example.com/doctor2.jpg"),
                ("doctor3@therapyapp.com", "Doctor789!", "Emeka", "Nwachukwu", "Counselor", 4, 80, "Enugu", "https://example.com/doctor3.jpg"),
                ("doctor4@therapyapp.com", "Doctor101!", "Fatima", "Ibrahim", "Psychiatrist", 10, 200, "Kano", "https://example.com/doctor4.jpg"),
                ("doctor5@therapyapp.com", "Doctor112!", "Chinedu", "Okeke", "Therapist", 5, 90, "Ibadan", "https://example.com/doctor5.jpg"),
            ]
            for email, pwd, fname, lname, title, exp, patients_count, loc, pic_url in doctor_data:
                doctor_user_id = await conn.fetchval(
                    """
                    INSERT INTO users (email, password_hash, is_doctor)
                    VALUES ($1, $2, $3)
                    RETURNING id
                    """,
                    email, hash_password(pwd), True
                )
                doctor_id = await conn.fetchval(
                    """
                    INSERT INTO doctors (user_id, first_name, last_name, title, bio, experience_years, patients_count, location, profile_picture_url)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                    """,
                    doctor_user_id, fname, lname, title, f"A {title.lower()} with {exp} years of experience.", exp, patients_count, loc, pic_url
                )
                doctors.append(doctor_id)
                logger.info(f"Doctor {fname} {lname} created with id: {doctor_id}")

            # Seed doctor availability slots
            logger.info("Seeding doctor availability slots...")
            today = datetime.now().date()
            for doctor_id in doctors:
                for i in range(5):  # 5 slots per doctor
                    # Each slot is on a different day in August, starting from today if today is in August, else from August 1
                    base_august = date(today.year, 8, 1)
                    if today.month == 8:
                        slot_date = today + timedelta(days=i)
                    else:
                        slot_date = base_august + timedelta(days=i)
                    slot_time = datetime.combine(slot_date, datetime.min.time()).replace(hour=9 + i % 4)
                    status = choice(['available', 'booked', 'expired'])
                    await conn.execute(
                        """
                        INSERT INTO doctor_availability_slots (doctor_id, available_at, status)
                        VALUES ($1, $2, $3)
                        """,
                        doctor_id, slot_time, status
                    )
                logger.info(f"Availability slots seeded for doctor id: {doctor_id}")

            # Seed doctor experiences
            logger.info("Seeding doctor experiences...")
            for i, doctor_id in enumerate(doctors):
                for j in range(5):
                    await conn.execute(
                        """
                        INSERT INTO doctors_experience (doctor_id, institution, position, start_date, end_date, description)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        doctor_id, f"Inst{i+1}_{j+1}", f"Position{j+1}", date(2015 + j, 1, 1), date(2019 + j, 12, 31),
                        f"Experience in role {j+1}"
                    )
                logger.info(f"Experiences seeded for doctor id: {doctor_id}")

            # Seed doctor reviews
            logger.info("Seeding doctor reviews...")
            for doctor_id in doctors:
                for i in range(5):
                    await conn.execute(
                        """
                        INSERT INTO doctors_reviews (doctor_id, user_id, rating, comment)
                        VALUES ($1, $2, $3, $4)
                        """,
                        doctor_id, patients[i % len(patients)], 4 + i % 2, f"Review {i+1} for doctor"
                    )
                logger.info(f"Reviews seeded for doctor id: {doctor_id}")

            # Seed doctor-patient relationships
            logger.info("Seeding doctor-patient relationships...")
            for doctor_id in doctors:
                for patient_id in patients[:3]:  # Link first 3 patients to each doctor
                    await conn.execute(
                        """
                        INSERT INTO doctors_patients (doctor_id, patient_id)
                        VALUES ($1, $2)
                        """,
                        doctor_id, patient_id
                    )
                logger.info(f"Relationships seeded for doctor id: {doctor_id}")

            # Seed appointments
            logger.info("Seeding appointments...")
            # Appointments start from today (or August 1 if not August) and go into coming days in August
            today = datetime.now().date()
            base_august = date(today.year, 8, 1)
            for i, (doctor_id, patient_id) in enumerate(zip(doctors, patients)):
                for j in range(5):
                    # Calculate appointment date in August
                    if today.month == 8:
                        appt_date = today + timedelta(days=i*5 + j)
                    else:
                        appt_date = base_august + timedelta(days=i*5 + j)
                    # Ensure we stay within August
                    if appt_date.month != 8:
                        break
                    slot_time = datetime.combine(appt_date, datetime.min.time()).replace(hour=10 + j, minute=0)
                    appointment_id = await conn.fetchval(
                        """
                        INSERT INTO appointments (doctor_id, patient_id, slot_time, complain, status)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id
                        """,
                        doctor_id, patient_id, slot_time, f'Issue {j+1}', 'confirmed' if j % 2 == 0 else 'pending'
                    )
                    logger.info(f"Appointment {j+1} created with id: {appointment_id}")

            # Seed appointments_summary
            logger.info("Seeding appointments_summary...")
            for i, doctor_id in enumerate(doctors):
                for j, patient_id in enumerate(patients[:3]):  # Link first 3 patients to each doctor
                    # Follow up date in August, after appointments
                    today = datetime.now().date()
                    base_august = date(today.year, 8, 1)
                    if today.month == 8:
                        follow_up_date = today + timedelta(days=10 + i + j)
                    else:
                        follow_up_date = base_august + timedelta(days=10 + i + j)
                    # Ensure we stay within August
                    if follow_up_date.month != 8:
                        follow_up_date = date(today.year, 8, 28)
                    follow_up_datetime = datetime.combine(follow_up_date, datetime.min.time()).replace(hour=10)
                    await conn.execute(
                        """
                        INSERT INTO appointments_summary (doctor_id, patient_id, diagnosis, notes, prescription, follow_up_date)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        doctor_id, patient_id,
                        f"Diagnosis {i + j + 1}",
                        f"Notes for patient {j + 1} with doctor {i + 1}",
                        f"Prescription {i + j + 1}: Take medication X",
                        follow_up_datetime
                    )
                logger.info(f"Summary seeded for doctor id: {doctor_id}")

            # Seed chat messages
            logger.info("Seeding chat messages...")
            for appointment_id in range(1, 6):  # Assuming 5 appointments
                for i in range(5):
                    await conn.execute(
                        """
                        INSERT INTO chat_messages (appointment_id, sender_id, receiver_id, message)
                        VALUES ($1, $2, $3, $4)
                        """,
                        appointment_id, patients[i % len(patients)], doctors[i % len(doctors)], f"Message {i+1}"
                    )
                logger.info(f"Chat messages seeded for appointment id: {appointment_id}")

            # Seed feed items
            logger.info("Seeding feed items...")
            feed_data = [
                ("Relaxation Tips", "article", "https://example.com/relax1", "<p>Tip 1...</p>", "Guide 1", patients[0]),
                ("Meditation Guide", "article", "https://example.com/relax2", "<p>Tip 2...</p>", "Guide 2", patients[1]),
                ("Yoga Video", "video", "https://example.com/video1", None, "Video 1", patients[2]),
                ("Calm Audio", "audio", "https://example.com/audio1", None, "Audio 1", patients[3]),
                ("Stress Relief", "article", "https://example.com/relax3", "<p>Tip 3...</p>", "Guide 3", patients[4]),
                ("Breathing Exercise", "video", "https://example.com/video2", None, "Video 2", patients[0]),
                ("Sleep Tips", "audio", "https://example.com/audio2", None, "Audio 2", patients[1]),
            ]
            for title, ctype, url, content, desc, user_id in feed_data:
                await conn.execute(
                    """
                    INSERT INTO feed_items (title, content_type, url, content, description, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    title, ctype, url, content, desc, user_id
                )
            logger.info("Feed items seeded.")

            # Seed video calls
            logger.info("Seeding video calls...")
            today = datetime.now().date()
            base_august = date(today.year, 8, 1)
            for i in range(5):
                # Video call start_time in August, matching appointment logic
                if today.month == 8:
                    call_date = today + timedelta(days=i)
                else:
                    call_date = base_august + timedelta(days=i)
                if call_date.month != 8:
                    break
                start_time = datetime.combine(call_date, datetime.min.time()).replace(hour=10)
                await conn.execute(
                    """
                    INSERT INTO video_calls (appointment_id, initiator_id, receiver_id, start_time, status)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    i + 1, patients[i % len(patients)], doctors[i % len(doctors)], start_time, 'initiated'
                )
            logger.info("Video calls seeded.")

            # Seed categories and products
            logger.info("Seeding categories...")
            categories = []
            cat_names = ["Wellness", "Mental Health", "Fitness", "Nutrition", "Sleep"]
            for name in cat_names:
                cat_id = await conn.fetchval(
                    """
                    INSERT INTO categories (name)
                    VALUES ($1)
                    RETURNING id
                    """,
                    name
                )
                categories.append(cat_id)
                logger.info(f"Category {name} created with id: {cat_id}")

            logger.info("Seeding products...")
            for i in range(7):
                await conn.execute(
                    """
                    INSERT INTO products (name, description, price, currency, image_urls, category_id, key_benefits, specifications)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
                    """,
                    f"Product {i+1}", f"Description for product {i+1}", 50000 + i * 1000, "NGN",
                    [f"https://example.com/product{i+1}.jpg"], categories[i % len(categories)],
                    [f"Benefit {i+1}", f"Benefit {i+2}"], f'[{{"name": "Weight", "value": "{i+1} lbs"}}]'
                )
            logger.info("Products seeded.")

            # Seed product reviews
            logger.info("Seeding product reviews...")
            for i in range(6):
                await conn.execute(
                    """
                    INSERT INTO product_reviews (id, product_id, user_id, rating, comment)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    f"rev_{i+1:03d}", i + 1, patients[i % len(patients)], 3 + i % 3, f"Review {i+1}"
                )
            logger.info("Product reviews seeded.")

            # Seed blog posts
            logger.info("Seeding blog posts...")
            for i in range(6):
                category_id = categories[i % len(categories)]
                await conn.execute(
                    """
                    INSERT INTO blog_posts (title, category_id, description, content_type, content_url, thumbnail_url, duration, mood_relevance, user_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9)
                    """,
                    f"Blog Post {i+1}", category_id, f"Description {i+1}",
                    ["article", "video", "audio"][i % 3],
                    f"<p>Content {i+1}</p>" if i % 3 == 0 else f"https://example.com/content{i+1}.{['mp4', 'mp3'][i % 2]}",
                    f"https://example.com/thumb{i+1}.jpg", 300 if i % 3 != 0 else None,
                    f'{{"Happy": 0.3, "Calm": 0.9, "Manic": 0.1, "Sad": 0.4, "Angry": 0.0}}',
                    patients[i % len(patients)]
                )
            logger.info("Blog posts seeded.")

            # Seed mood recommendations
            logger.info("Seeding mood recommendations...")
            for i, patient_id in enumerate(patients):
                await conn.execute(
                    """
                    INSERT INTO mood_recommendations (id, user_id, current_mood)
                    VALUES ($1, $2, $3)
                    """,
                    i + 1, patient_id, ["Happy", "Calm", "Manic", "Sad", "Angry"][i % 5]
                )
            logger.info("Mood recommendations seeded.")
        else:
            logger.info("Users already exist. Skipping seeding.")