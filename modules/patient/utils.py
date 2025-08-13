


from shared.db import db
import datetime

async def get_patient_stats():
    """
    Returns a dictionary with:
        - total_patients: Total number of patients
        - total_active_patients: Patients with account_status = 'active'
        - total_inactive_patients: Patients with account_status = 'inactive'
        - total_subscribed_patients: Patients with account_type = 'subscribe'
        - total_appointments_today: Appointments scheduled for current date
    """
    async with db.get_connection() as conn:
        # Total patients
        total_patients = await conn.fetchval("SELECT COUNT(*) FROM patients")
        # Total active patients
        total_active_patients = await conn.fetchval(
            "SELECT COUNT(*) FROM patients WHERE account_status = 'active'"
        )
        # Total inactive patients
        total_inactive_patients = await conn.fetchval(
            "SELECT COUNT(*) FROM patients WHERE account_status = 'inactive'"
        )
        # Total subscribed patients
        total_subscribed_patients = await conn.fetchval(
            "SELECT COUNT(*) FROM patients WHERE account_type = 'subscribe'"
        )
        # Total appointments scheduled for current date
        total_appointments_today = await conn.fetchval(
            """
            SELECT COUNT(*) FROM appointments
            WHERE DATE(slot_time) = CURRENT_DATE
            """
        )

    return {
        "total_patients": total_patients or 0,
        "total_active_patients": total_active_patients or 0,
        "total_inactive_patients": total_inactive_patients or 0,
        "total_subscribed_patients": total_subscribed_patients or 0,
        "total_appointments_today": total_appointments_today or 0,
    }
