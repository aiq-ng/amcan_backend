from .models import DoctorCreate, DoctorResponse
from shared.db import db
import datetime

class DoctorManager:
    
    @staticmethod
    async def create_doctor(doctor_item: DoctorCreate, user_id: int) -> dict:
        print('creating doctor hit')

        async with db.get_connection() as conn:
            # Insert into doctors table
            row = await conn.fetchrow(
                """
                INSERT INTO doctors (user_id, first_name, last_name, title, bio, experience_years, patients_count, location, profile_picture_url)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, user_id, first_name, last_name, title, bio, experience_years, patients_count, location, rating, profile_picture_url, created_at
                """,
                user_id,
                doctor_item.first_name,
                doctor_item.last_name,
                doctor_item.title,
                doctor_item.bio,
                doctor_item.experience_years,
                doctor_item.patients_count,
                doctor_item.location,
                doctor_item.profile_picture_url
            )

            # Update the user to set is_doctor = TRUE
            await conn.execute(
                """
                UPDATE users
                SET is_doctor = TRUE
                WHERE id = $1
                """,
                user_id
            )

            result = dict(row)
            print('doctor created:', result)

            # Convert datetime objects to ISO format strings
            if 'created_at' in result and isinstance(result['created_at'], datetime):
                result['created_at'] = result['created_at'].isoformat()

            return result

    @staticmethod
    async def get_doctors(
        page: int = 1,
        page_size: int = 10,
        search: str = None,
        location: str = None,
        min_rating: float = None,
        max_rating: float = None,
        specialty: str = None,
    ) -> dict:
        """
        Fetch doctors with optional filters, search, and pagination.
        Returns a dict with 'data', 'total', 'page', 'page_size'.
        """
        filters = []
        params = []
        param_idx = 1

        # Search by name, title, bio, or location
        if search:
            filters.append(
                f"(d.first_name ILIKE ${param_idx} OR d.last_name ILIKE ${param_idx} OR d.title ILIKE ${param_idx} OR d.bio ILIKE ${param_idx} OR d.location ILIKE ${param_idx})"
            )
            params.append(f"%{search}%")
            param_idx += 1

        # Filter by location
        if location:
            filters.append(f"d.location ILIKE ${param_idx}")
            params.append(f"%{location}%")
            param_idx += 1

        # Filter by minimum rating
        if min_rating is not None:
            filters.append(f"d.rating >= ${param_idx}")
            params.append(min_rating)
            param_idx += 1

        # Filter by maximum rating
        if max_rating is not None:
            filters.append(f"d.rating <= ${param_idx}")
            params.append(max_rating)
            param_idx += 1

        # Filter by specialty (assuming specialty is stored in title or a separate field)
        if specialty:
            filters.append(f"d.title ILIKE ${param_idx}")
            params.append(f"%{specialty}%")
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        # Calculate offset for pagination
        offset = (page - 1) * page_size
        limit = page_size

        # Count query for total
        count_query = f"""
            SELECT COUNT(*) FROM doctors d
            {where_clause}
        """

        # Data query with pagination
        # Fix: Use single $-style parameter placeholders, not double $$
        data_query = f"""
            SELECT 
                d.id AS doctor_id,
                d.user_id,
                d.first_name,
                d.last_name,
                d.title,
                d.bio,
                d.experience_years,
                d.patients_count,
                d.location,
                d.rating,
                d.profile_picture_url,
                d.created_at,
                (
                    SELECT JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'review_id', dr.id,
                            'user_id', dr.user_id,
                            'rating', dr.rating,
                            'comment', dr.comment,
                            'created_at', dr.created_at
                        )
                    )
                    FROM doctors_reviews dr 
                    WHERE dr.doctor_id = d.id
                ) AS reviews,
                (
                    SELECT JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'experience_id', de.id,
                            'institution', de.institution,
                            'position', de.position,
                            'start_date', de.start_date,
                            'end_date', de.end_date,
                            'description', de.description,
                            'created_at', de.created_at
                        )
                    )
                    FROM doctors_experience de 
                    WHERE de.doctor_id = d.id
                ) AS experiences,
                (
                    SELECT JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'slot_id', das.id,
                            'available_at', das.available_at,
                            'status', das.status,
                            'created_at', das.created_at
                        )
                    )
                    FROM doctor_availability_slots das 
                    WHERE das.doctor_id = d.id
                ) AS availability_slots,
                (
                    SELECT COUNT(*) 
                    FROM appointments a 
                    WHERE a.doctor_id = d.id 
                    AND DATE(a.slot_time) = CURRENT_DATE
                ) AS appointment_count_today,
                (
                    SELECT COUNT(DISTINCT dp.patient_id) 
                    FROM doctors_patients dp 
                    WHERE dp.doctor_id = d.id
                ) AS patient_count,
                JSONB_AGG(
                    JSONB_BUILD_OBJECT(
                        'appointment_id', a.id,
                        'patient_id', a.patient_id,
                        'slot_time', a.slot_time,
                        'complain', a.complain,
                        'status', a.status
                    )
                ) FILTER (WHERE a.id IS NOT NULL) AS appointments_today
            FROM doctors d
            LEFT JOIN appointments a ON d.id = a.doctor_id AND DATE(a.slot_time) = CURRENT_DATE
            LEFT JOIN doctors_reviews dr ON d.id = dr.doctor_id
            LEFT JOIN doctors_experience de ON d.id = de.doctor_id
            LEFT JOIN doctors_patients dp ON d.id = dp.doctor_id
            {where_clause}
            GROUP BY d.id, d.user_id, d.first_name, d.last_name, d.title, d.bio, d.experience_years, d.patients_count, d.location, d.rating, d.profile_picture_url, d.created_at
            ORDER BY d.rating DESC NULLS LAST, d.created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """

        params_for_data = params.copy()
        params_for_data.append(limit)
        params_for_data.append(offset)

        async with db.get_connection() as conn:
            total = await conn.fetchval(count_query, *params)
            rows = await conn.fetch(data_query, *params_for_data)
            result = [dict(row) for row in rows] if rows else []
            meta_data = {"total": total,
                "page": page,
                "page_size": page_size,}
            return {
                "doctors": result,
                "meta_data": meta_data,
            }

    @staticmethod
    async def get_doctor(doctor_id: int) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    d.id AS doctor_id,
                    d.user_id,
                    d.first_name,
                    d.last_name,
                    d.title,
                    d.bio,
                    d.experience_years,
                    d.patients_count,
                    d.location,
                    d.rating,
                    d.profile_picture_url,
                    d.created_at,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'review_id', dr.id,
                                'user_id', dr.user_id,
                                'rating', dr.rating,
                                'comment', dr.comment,
                                'created_at', dr.created_at
                            )
                        )
                        FROM doctors_reviews dr 
                        WHERE dr.doctor_id = d.id
                    ) AS reviews,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'experience_id', de.id,
                                'institution', de.institution,
                                'position', de.position,
                                'start_date', de.start_date,
                                'end_date', de.end_date,
                                'description', de.description,
                                'created_at', de.created_at
                            )
                        )
                        FROM doctors_experience de 
                        WHERE de.doctor_id = d.id
                    ) AS experiences,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'slot_id', das.id,
                                'available_at', das.available_at,
                                'status', das.status,
                                'created_at', das.created_at
                            )
                        )
                        FROM doctor_availability_slots das 
                        WHERE das.doctor_id = d.id
                    ) AS availability_slots,
                    (
                        SELECT COUNT(*) 
                        FROM appointments a 
                        WHERE a.doctor_id = d.id 
                        AND DATE(a.slot_time) = CURRENT_DATE
                    ) AS appointment_count_today,
                    (
                        SELECT COUNT(DISTINCT dp.patient_id) 
                        FROM doctors_patients dp 
                        WHERE dp.doctor_id = d.id
                    ) AS patient_count,
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'appointment_id', a.id,
                            'patient_id', a.patient_id,
                            'slot_time', a.slot_time,
                            'complain', a.complain,
                            'status', a.status
                        )
                    ) FILTER (WHERE a.id IS NOT NULL) AS appointments_today
                FROM doctors d
                LEFT JOIN appointments a ON d.id = a.doctor_id AND DATE(a.slot_time) = CURRENT_DATE
                LEFT JOIN doctors_reviews dr ON d.id = dr.doctor_id
                LEFT JOIN doctors_experience de ON d.id = de.doctor_id
                LEFT JOIN doctors_patients dp ON d.id = dp.doctor_id
                WHERE d.id = $1
                GROUP BY d.id, d.user_id, d.first_name, d.last_name, d.title, d.bio, d.experience_years, d.patients_count, d.location, d.rating, d.profile_picture_url, d.created_at
                """,
                doctor_id
            )
            if row:
                result = dict(row)
                # Convert datetime objects to ISO format strings
                # if 'created_at' in result and isinstance(result['created_at'], datetime):
                #     result['created_at'] = result['created_at'].isoformat()
                # if result['reviews']:
                #     result['reviews'] = [
                #         {**review, 'created_at': review['created_at'].isoformat()}
                #         for review in result['reviews']
                #     ]
                # if result['experiences']:
                #     result['experiences'] = [
                #         {**exp, 'start_date': exp['start_date'].isoformat(), 'end_date': exp['end_date'].isoformat() if exp['end_date'] else None, 'created_at': exp['created_at'].isoformat()}
                #         for exp in result['experiences']
                #     ]
                # if result['availability_slots']:
                #     result['availability_slots'] = [
                #         {**slot, 'available_at': slot['available_at'].isoformat(), 'created_at': slot['created_at'].isoformat()}
                #         for slot in result['availability_slots']
                #     ]
                # if result['appointments_today']:
                #     result['appointments_today'] = [
                #         {**appt, 'slot_time': appt['slot_time'].isoformat()}
                #         for appt in result['appointments_today']
                #     ]
                return result
            return None

    async def get_doctor_by_user_id(user_id: int) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    d.id AS doctor_id,
                    d.user_id,
                    d.first_name,
                    d.last_name,
                    d.title,
                    d.bio,
                    d.experience_years,
                    d.patients_count,
                    d.location,
                    d.rating,
                    d.profile_picture_url,
                    d.created_at,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'review_id', dr.id,
                                'user_id', dr.user_id,
                                'rating', dr.rating,
                                'comment', dr.comment,
                                'created_at', dr.created_at
                            )
                        )
                        FROM doctors_reviews dr 
                        WHERE dr.doctor_id = d.id
                    ) AS reviews,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'experience_id', de.id,
                                'institution', de.institution,
                                'position', de.position,
                                'start_date', de.start_date,
                                'end_date', de.end_date,
                                'description', de.description,
                                'created_at', de.created_at
                            )
                        )
                        FROM doctors_experience de 
                        WHERE de.doctor_id = d.id
                    ) AS experiences,
                    (
                        SELECT JSONB_AGG(
                            JSONB_BUILD_OBJECT(
                                'slot_id', das.id,
                                'available_at', das.available_at,
                                'status', das.status,
                                'created_at', das.created_at
                            )
                        )
                        FROM doctor_availability_slots das 
                        WHERE das.doctor_id = d.id
                    ) AS availability_slots,
                    (
                        SELECT COUNT(*) 
                        FROM appointments a 
                        WHERE a.doctor_id = d.id 
                        AND DATE(a.slot_time) = CURRENT_DATE
                    ) AS appointment_count_today,
                    (
                        SELECT COUNT(DISTINCT dp.patient_id) 
                        FROM doctors_patients dp 
                        WHERE dp.doctor_id = d.id
                    ) AS patient_count,
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'appointment_id', a.id,
                            'patient_id', a.patient_id,
                            'slot_time', a.slot_time,
                            'complain', a.complain,
                            'status', a.status
                        )
                    ) FILTER (WHERE a.id IS NOT NULL) AS appointments_today
                FROM doctors d
                LEFT JOIN appointments a ON d.id = a.doctor_id AND DATE(a.slot_time) = CURRENT_DATE
                LEFT JOIN doctors_reviews dr ON d.id = dr.doctor_id
                LEFT JOIN doctors_experience de ON d.id = de.doctor_id
                LEFT JOIN doctors_patients dp ON d.id = dp.doctor_id
                WHERE d.user_id = $1
                GROUP BY d.id, d.user_id, d.first_name, d.last_name, d.title, d.bio, d.experience_years, d.patients_count, d.location, d.rating, d.profile_picture_url, d.created_at
                """,
                user_id
            )
            if row:
                result = dict(row)
                # # Convert datetime objects to ISO format strings
                # if 'created_at' in result and isinstance(result['created_at'], datetime):
                #     result['created_at'] = result['created_at'].isoformat()
                # if result['reviews']:
                #     result['reviews'] = [
                #         {**review, 'created_at': review['created_at'].isoformat()}
                #         for review in result['reviews']
                #     ]
                # if result['experiences']:
                #     result['experiences'] = [
                #         {**exp, 'start_date': exp['start_date'].isoformat(), 'end_date': exp['end_date'].isoformat() if exp['end_date'] else None, 'created_at': exp['created_at'].isoformat()}
                #         for exp in result['experiences']
                #     ]
                # if result['availability_slots']:
                #     result['availability_slots'] = [
                #         {**slot, 'available_at': slot['available_at'].isoformat(), 'created_at': slot['created_at'].isoformat()}
                #         for slot in result['availability_slots']
                #     ]
                # if result['appointments_today']:
                #     result['appointments_today'] = [
                #         {**appt, 'slot_time': appt['slot_time'].isoformat()}
                #         for appt in result['appointments_today']
                #     ]
                return result
            return None

    @staticmethod
    async def add_review(doctor_id: int, user_id: int, rating: int, comment: str) -> dict:
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO doctors_reviews (doctor_id, user_id, rating, comment)
                VALUES ($1, $2, $3, $4)
                RETURNING id, doctor_id, user_id, rating, comment, created_at
                """,
                doctor_id,
                user_id,
                rating,
                comment
            )
            if row:
                result = dict(row)
                if 'created_at' in result and isinstance(result['created_at'], datetime):
                    result['created_at'] = result['created_at'].isoformat()
                return result
            return None

    @staticmethod
    async def create_availability_slot(doctor_id: int, available_at: datetime.datetime):
        """
        Creates a new availability slot for a doctor.

        Args:
            doctor_id: The ID of the doctor.
            available_at: A timezone-aware datetime object representing the start
                        time of the availability slot.

        Returns:
            A dictionary representing the newly created availability slot,
            with datetime objects converted to ISO 8601 strings.

        Raises:
            ValueError: If the doctor is not found, or if an availability slot
                        already exists for the given doctor and time.
            TypeError: If 'available_at' is not a timezone-aware datetime object.
        """
        if not isinstance(available_at, datetime.datetime):
            raise TypeError("available_at must be a datetime object.")
        if available_at.tzinfo is None:
            raise TypeError("available_at must be a timezone-aware datetime object.")

        async with db.get_connection() as conn:
            # Check if doctor exists
            doctor = await conn.fetchrow(
                """
                SELECT id FROM doctors WHERE id = $1
                """,
                doctor_id
            )
            if not doctor:
                raise ValueError("Doctor not found")

            # Check if slot already exists for the exact time (timezone-aware comparison)
            existing_slot = await conn.fetchrow(
                """
                SELECT id FROM doctor_availability_slots 
                WHERE doctor_id = $1 AND available_at = $2
                """,
                doctor_id,
                available_at
            )
            if existing_slot:
                raise ValueError("Availability slot already exists for this time")

            # Create new availability slot
            row = await conn.fetchrow(
                """
                INSERT INTO doctor_availability_slots (doctor_id, available_at, status)
                VALUES ($1, $2, 'available')
                RETURNING id, doctor_id, available_at, status, created_at
                """,
                doctor_id,
                available_at
            )

            if row:
                result = dict(row)
                # Convert datetime objects to ISO 8601 strings for consistent output
                # isoformat() will include timezone offset since they are timezone-aware
                if 'created_at' in result and isinstance(result['created_at'], datetime.datetime):
                    result['created_at'] = result['created_at'].isoformat()
                if 'available_at' in result and isinstance(result['available_at'], datetime.datetime):
                    result['available_at'] = result['available_at'].isoformat()
                return result
            
            # This part should ideally not be reached if INSERT RETURNING is successful,
            # but good to have a fallback or handle specific cases.
            return None


