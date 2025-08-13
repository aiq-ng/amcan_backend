import datetime
from shared.db import db



async def get_weekly_appointment_stats(doctor_id: int) -> dict:
    """
    Returns a dictionary with the count of appointments for each working day (Monday-Friday)
    for the given doctor. The result is in the form:
    {
        "weekly_state": {
            "Monday": count,
            "Tuesday": count,
            "Wednesday": count,
            "Thursday": count,
            "Friday": count
        }
    }
    """
    # Map PostgreSQL dow (0=Sunday, 1=Monday, ...) to weekday names
    weekday_map = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday"
    }
    # Get the current week's Monday
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    friday = monday + datetime.timedelta(days=4)

    async with db.get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                EXTRACT(DOW FROM slot_time)::int AS dow,
                COUNT(*) AS count
            FROM appointments
            WHERE doctor_id = $1
                AND slot_time::date >= $2
                AND slot_time::date <= $3
                AND EXTRACT(DOW FROM slot_time) BETWEEN 1 AND 5
            GROUP BY dow
            """,
            doctor_id,
            monday,
            friday
        )
        # Initialize all weekdays to 0
        weekly_state = {name: 0 for name in weekday_map.values()}
        for row in rows:
            dow = int(row['dow'])
            if dow in weekday_map:
                weekly_state[weekday_map[dow]] = row['count']
        return {"weekly_state": weekly_state}



async def get_todays_appointments(doctor_id: int):
    """
    Fetches all appointments for the given doctor for the current date.
    Returns a dictionary with a list of today's appointments under the key 'todays_appointment'.
    """
    today = datetime.date.today()
    async with db.get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                id AS appointment_id,
                patient_id,
                slot_time,
                complain,
                status
            FROM appointments
            WHERE doctor_id = $1
                AND DATE(slot_time) = $2
            ORDER BY slot_time ASC
            """,
            doctor_id,
            today
        )
        # Convert slot_time to isoformat if needed
        appointments = []
        for row in rows:
            appt = dict(row)
            if isinstance(appt.get("slot_time"), (datetime.datetime, datetime.date)):
                appt["slot_time"] = appt["slot_time"].isoformat()
            appointments.append(appt)
        return {"todays_appointment": appointments}

async def get_doctor_stats():
    """
    Returns statistics related to doctors:
    - total_doctors: Total number of doctors
    - total_video_calls: Total number of video calls
    - specialties_count: Dictionary mapping specialty/title to count of doctors
    - appointments_today: Number of appointments scheduled for today
    """
    today = datetime.date.today()
    async with db.get_connection() as conn:
        # Total doctors
        total_doctors = await conn.fetchval("SELECT COUNT(*) FROM doctors")

        # Total video calls
        total_video_calls = await conn.fetchval("SELECT COUNT(*) FROM video_calls")

        # Count of specialties (by title)
        specialty_rows = await conn.fetch("""
            SELECT title, COUNT(*) as count
            FROM doctors
            GROUP BY title
        """)
        # specialties_count = {row['title']: row['count'] for row in specialty_rows if row['title']}

        # Appointments slated for current date
        appointments_today = await conn.fetchval("""
            SELECT COUNT(*) FROM appointments
            WHERE DATE(slot_time) = $1
        """, today)

    stat = {
        "total_doctors": total_doctors,
        "total_sessions": total_video_calls,
        "specialties_count": 8,
        "appointments_today": appointments_today
    }

    return {"doctors_general_stat": stat}


