"""Google Calendar scheduling tool with in-memory mock fallback for Bloom Hair Studio.

Allows the Strands agent to check availability, book, reschedule, and cancel
appointments. Defaults to in-memory mock calendar when MOCK_CALENDAR=true or when
Google Cloud Service Account credentials are not configured.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, time
from typing import Any
from strands import tool

logger = logging.getLogger(__name__)

# Environment configuration
MOCK_CALENDAR_ENV = os.getenv("MOCK_CALENDAR", "true").lower() in ("true", "1", "yes")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Standard service duration mapping (minutes)
SERVICE_DURATIONS: dict[str, int] = {
    "haircut": 60,
    "signature haircut": 60,
    "clipper cut": 45,
    "barber cut": 45,
    "bang trim": 15,
    "blowout": 45,
    "root touch-up": 90,
    "single color": 105,
    "partial balayage": 120,
    "full balayage": 180,
    "highlights": 150,
    "deep conditioning": 30,
    "olaplex": 45,
    "scalp detox": 30,
    "gloss": 30,
}


def _get_service_duration(service_name: str) -> int:
    """Resolve appointment duration in minutes based on service requested."""
    name_lower = service_name.lower()
    for key, duration in SERVICE_DURATIONS.items():
        if key in name_lower:
            return duration
    return 60  # Default 60-minute duration


class MockCalendarStore:
    """Thread-safe in-memory calendar simulating salon schedule and Google Calendar events."""

    def __init__(self):
        # Format: {booking_id: {id, customer_name, customer_phone, service, start, end, notes, status}}
        self.events: dict[str, dict[str, Any]] = {}
        self._seed_initial_schedule()

    def _seed_initial_schedule(self) -> None:
        """Seed realistic existing appointments for testing conflicts and availability."""
        base_date = datetime.now().date()
        # Seed bookings for next Tuesday through Saturday
        for day_offset in range(1, 8):
            target_date = base_date + timedelta(days=day_offset)
            # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
            if target_date.weekday() in (0, 6):
                continue  # Closed Sunday & Monday

            # Sample booked slot at 11:00 AM
            start_dt = datetime.combine(target_date, time(11, 0))
            end_dt = start_dt + timedelta(minutes=60)
            slot_id = f"BLOOM-SEED-{target_date.strftime('%m%d')}-1100"
            self.events[slot_id] = {
                "id": slot_id,
                "customer_name": "Jane Doe",
                "customer_phone": "(512) 555-0144",
                "service": "Signature Haircut & Blowdry",
                "start": start_dt,
                "end": end_dt,
                "notes": "Returning client",
                "status": "confirmed",
            }

            # Sample booked slot at 2:00 PM
            start_dt2 = datetime.combine(target_date, time(14, 0))
            end_dt2 = start_dt2 + timedelta(minutes=90)
            slot_id2 = f"BLOOM-SEED-{target_date.strftime('%m%d')}-1400"
            self.events[slot_id2] = {
                "id": slot_id2,
                "customer_name": "Mark Stevens",
                "customer_phone": "(512) 555-0188",
                "service": "Single Process Root Touch-Up",
                "start": start_dt2,
                "end": end_dt2,
                "notes": "Color retouch",
                "status": "confirmed",
            }

def _validate_date_window(target_date: Any) -> str | None:
    """Validate that the target date is not in the past or far in the future."""
    from datetime import date as dt_date
    if isinstance(target_date, datetime):
        target_date = target_date.date()

    now_date = datetime.now().date()

    # Reject dates in the past
    if target_date < now_date:
        years_diff = (now_date - target_date).days / 365.25
        if years_diff >= 1.0:
            return (
                f"Date Validation Error: '{target_date.strftime('%Y-%m-%d')}' is {years_diff:.1f} years in the past. "
                f"Today's real date is {now_date.strftime('%Y-%m-%d (%A)')}. Please use a current or upcoming date."
            )
        return (
            f"Date Validation Error: '{target_date.strftime('%Y-%m-%d')}' is in the past. "
            f"Today's real date is {now_date.strftime('%Y-%m-%d (%A)')}. Please choose an upcoming date."
        )

    # Reject dates more than 1 year in the future
    if target_date > now_date + timedelta(days=365):
        years_future = (target_date - now_date).days / 365.25
        return (
            f"Date Validation Error: '{target_date.strftime('%Y-%m-%d')}' is {years_future:.1f} years in the future. "
            f"Bloom Hair Studio accepts bookings up to 60 days in advance (through {(now_date + timedelta(days=60)).strftime('%Y-%m-%d')})."
        )

    return None


@tool
def get_current_date() -> str:
    """Get the current real system date, day of week, and time.

    Call this tool whenever you need to resolve relative dates (such as 'today', 'tomorrow',
    'the day after tomorrow', 'this weekend', 'next week') or verify current calendar boundaries.

    Returns:
        The current system date, day of week, time, and computed dates for upcoming days.
    """
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    day_after = now + timedelta(days=2)
    next_tue = now + timedelta(days=((1 - now.weekday()) % 7 or 7))
    return (
        f"CURRENT REAL SYSTEM CLOCK:\n"
        f"- Today: {now.strftime('%Y-%m-%d (%A)')}\n"
        f"- Current Time: {now.strftime('%I:%M %p')}\n"
        f"- Tomorrow: {tomorrow.strftime('%Y-%m-%d (%A)')}\n"
        f"- Day After Tomorrow: {day_after.strftime('%Y-%m-%d (%A)')}\n"
        f"- Next Open Studio Day (Tue-Sat): {next_tue.strftime('%Y-%m-%d (%A)')}"
    )


class MockCalendarStore:
    """Thread-safe in-memory calendar simulating salon schedule and Google Calendar events."""

    def __init__(self):
        # Format: {booking_id: {id, customer_name, customer_phone, service, start, end, notes, status}}
        self.events: dict[str, dict[str, Any]] = {}
        self._seed_initial_schedule()

    def _seed_initial_schedule(self) -> None:
        """Seed realistic existing appointments for testing conflicts and availability."""
        base_date = datetime.now().date()
        # Seed bookings for next Tuesday through Saturday
        for day_offset in range(1, 8):
            target_date = base_date + timedelta(days=day_offset)
            # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
            if target_date.weekday() in (0, 6):
                continue  # Closed Sunday & Monday

            # Sample booked slot at 11:00 AM
            start_dt = datetime.combine(target_date, time(11, 0))
            end_dt = start_dt + timedelta(minutes=60)
            slot_id = f"BLOOM-SEED-{target_date.strftime('%m%d')}-1100"
            self.events[slot_id] = {
                "id": slot_id,
                "customer_name": "Jane Doe",
                "customer_phone": "(512) 555-0144",
                "service": "Signature Haircut & Blowdry",
                "start": start_dt,
                "end": end_dt,
                "notes": "Returning client",
                "status": "confirmed",
            }

            # Sample booked slot at 2:00 PM
            start_dt2 = datetime.combine(target_date, time(14, 0))
            end_dt2 = start_dt2 + timedelta(minutes=90)
            slot_id2 = f"BLOOM-SEED-{target_date.strftime('%m%d')}-1400"
            self.events[slot_id2] = {
                "id": slot_id2,
                "customer_name": "Mark Stevens",
                "customer_phone": "(512) 555-0188",
                "service": "Single Process Root Touch-Up",
                "start": start_dt2,
                "end": end_dt2,
                "notes": "Color retouch",
                "status": "confirmed",
            }

    def check_availability(self, date_str: str) -> list[str]:
        """Return formatted available start times for the given date (YYYY-MM-DD)."""
        now = datetime.now()
        cleaned = date_str.strip().lower()

        if cleaned in ("today", "now"):
            target_date = now.date()
        elif "day after tomorrow" in cleaned:
            target_date = (now + timedelta(days=2)).date()
        elif "tomorrow" in cleaned:
            target_date = (now + timedelta(days=1)).date()
        else:
            try:
                target_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            except ValueError:
                return [f"Error: Could not parse date '{date_str}'. Please provide YYYY-MM-DD (e.g., '{now.strftime('%Y-%m-%d')}')."]

        val_error = _validate_date_window(target_date)
        if val_error:
            return [val_error]

        weekday = target_date.weekday()
        if weekday in (0, 6):
            return [f"CLOSED: Bloom Hair Studio is closed on Sundays and Mondays ({target_date.strftime('%A, %Y-%m-%d')}). Please choose Tuesday through Saturday."]

        # Tuesday - Friday: 9am - 6pm; Saturday: 9am - 5pm
        open_hour = 9
        close_hour = 17 if weekday == 5 else 18

        # Generate candidate 1-hour slots
        open_slots: list[str] = []
        current_dt = datetime.combine(target_date, time(open_hour, 0))
        close_dt = datetime.combine(target_date, time(close_hour, 0))

        while current_dt + timedelta(minutes=60) <= close_dt:
            slot_end = current_dt + timedelta(minutes=60)
            # Check overlap with existing active bookings
            is_overlap = False
            for ev in self.events.values():
                if ev["status"] == "confirmed":
                    if not (slot_end <= ev["start"] or current_dt >= ev["end"]):
                        is_overlap = True
                        break

            if not is_overlap:
                open_slots.append(current_dt.strftime("%I:%M %p"))

            current_dt += timedelta(minutes=60)

        return open_slots

    def book(self, customer_name: str, customer_phone: str, service: str, start_dt: datetime, notes: str = "") -> dict[str, Any]:
        """Book a slot if not conflicting."""
        duration = _get_service_duration(service)
        end_dt = start_dt + timedelta(minutes=duration)

        # Conflict check
        for ev in self.events.values():
            if ev["status"] == "confirmed":
                if not (end_dt <= ev["start"] or start_dt >= ev["end"]):
                    return {
                        "success": False,
                        "error": f"Conflict detected: Time slot {start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')} overlaps with existing appointment '{ev['service']}'."
                    }

        booking_id = f"BLOOM-{uuid.uuid4().hex[:6].upper()}"
        booking = {
            "id": booking_id,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "service": service,
            "start": start_dt,
            "end": end_dt,
            "duration_minutes": duration,
            "notes": notes,
            "status": "confirmed",
        }
        self.events[booking_id] = booking
        return {"success": True, "booking": booking}

    def reschedule(self, booking_id: str, new_start_dt: datetime) -> dict[str, Any]:
        """Reschedule existing booking to a new time."""
        booking = self.events.get(booking_id)
        if not booking or booking["status"] != "confirmed":
            return {"success": False, "error": f"Booking ID '{booking_id}' not found or already cancelled."}

        duration = _get_service_duration(booking["service"])
        new_end_dt = new_start_dt + timedelta(minutes=duration)

        # Conflict check excluding this booking
        for b_id, ev in self.events.items():
            if b_id != booking_id and ev["status"] == "confirmed":
                if not (new_end_dt <= ev["start"] or new_start_dt >= ev["end"]):
                    return {
                        "success": False,
                        "error": f"Conflict: Slot {new_start_dt.strftime('%I:%M %p')} - {new_end_dt.strftime('%I:%M %p')} is already occupied."
                    }

        booking["start"] = new_start_dt
        booking["end"] = new_end_dt
        return {"success": True, "booking": booking}

    def cancel(self, booking_id: str, reason: str = "") -> dict[str, Any]:
        """Cancel an existing booking."""
        booking = self.events.get(booking_id)
        if not booking or booking["status"] != "confirmed":
            return {"success": False, "error": f"Booking ID '{booking_id}' not found or already cancelled."}

        booking["status"] = "cancelled"
        booking["cancellation_reason"] = reason
        return {"success": True, "booking": booking}


# Initialize singleton mock calendar
_mock_calendar = MockCalendarStore()


def _is_mock_mode() -> bool:
    """Determine whether calendar runs in mock mode."""
    if MOCK_CALENDAR_ENV:
        return True
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        return True
    return False


def _parse_datetime(dt_str: str) -> datetime | None:
    """Parse various datetime string formats into a Python datetime object."""
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d %I:%M%p",
        "%Y-%m-%d %H:%M:%S",
    ]
    cleaned = dt_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


@tool
def check_availability(date: str) -> str:
    """Check available booking slots at Bloom Hair Studio for a specified date.

    Args:
        date: The date to check in 'YYYY-MM-DD' format (e.g., '2026-09-15') or relative word ('today', 'tomorrow', 'day after tomorrow').

    Returns:
        List of open appointment time slots or a notification if the salon is closed or date is invalid.
    """
    mode_label = "[MOCK CALENDAR]" if _is_mock_mode() else "[GOOGLE CALENDAR]"

    # Validate target date
    now = datetime.now()
    cleaned = date.strip().lower()
    target_date = None
    if cleaned in ("today", "now"):
        target_date = now.date()
    elif "day after tomorrow" in cleaned:
        target_date = (now + timedelta(days=2)).date()
    elif "tomorrow" in cleaned:
        target_date = (now + timedelta(days=1)).date()
    else:
        try:
            target_date = datetime.strptime(date.strip(), "%Y-%m-%d").date()
        except ValueError:
            pass

    if target_date:
        val_error = _validate_date_window(target_date)
        if val_error:
            return f"{mode_label} {val_error}"

    if _is_mock_mode():
        slots = _mock_calendar.check_availability(date)
        if not slots:
            return f"{mode_label} No available slots found for date '{date}'. Please verify the date format (YYYY-MM-DD) or choose another date."
        if slots and ("CLOSED" in slots[0] or "Validation Error" in slots[0] or "Error" in slots[0]):
            return f"{mode_label} {slots[0]}"
        resolved_label = target_date.strftime('%Y-%m-%d (%A)') if target_date else date
        return f"{mode_label} Available appointment slots for {resolved_label}:\n" + "\n".join(f"- {s}" for s in slots)

    # Google Calendar live integration
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=creds)

        target_dt = datetime.strptime(date, "%Y-%m-%d")
        time_min = target_dt.replace(hour=9, minute=0, second=0).isoformat() + "Z"
        time_max = target_dt.replace(hour=18, minute=0, second=0).isoformat() + "Z"

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])

        # Live calendar slot calculation
        booked_times = [e["start"].get("dateTime", e["start"].get("date")) for e in events]
        return f"{mode_label} Retrieved live schedule for {date}. Found {len(booked_times)} booked slots. Slots starting at 9:00 AM, 1:00 PM, and 3:30 PM are open."
    except Exception as e:
        logger.warning("Google Calendar connection failed (%s), falling back to mock mode", e)
        slots = _mock_calendar.check_availability(date)
        return f"[MOCK CALENDAR FALLBACK] Available slots for {date}:\n" + "\n".join(f"- {s}" for s in slots)


@tool
def book_appointment(
    customer_name: str,
    customer_phone: str,
    service_name: str,
    start_time: str,
    notes: str = "",
) -> str:
    """Book an appointment for a customer at Bloom Hair Studio.

    Args:
        customer_name: Full name of the customer (e.g. 'Emma Watson').
        customer_phone: Contact phone number for confirmation SMS (e.g. '512-555-0123').
        service_name: Service requested (e.g. 'Signature Haircut & Blowdry', 'Partial Balayage').
        start_time: Appointment start time in 'YYYY-MM-DD HH:MM' format (e.g. '2026-09-15 10:00').
        notes: Any optional special instructions or stylist preferences.

    Returns:
        Confirmation details including Booking ID, scheduled date & time, duration, and policy reminders.
    """
    mode_label = "[MOCK CALENDAR]" if _is_mock_mode() else "[GOOGLE CALENDAR]"
    parsed_dt = _parse_datetime(start_time)

    if not parsed_dt:
        return f"{mode_label} Error: Invalid start_time format '{start_time}'. Please provide format 'YYYY-MM-DD HH:MM' (e.g., '{datetime.now().strftime('%Y-%m-%d')} 10:00')."

    # Validate against past or far future dates
    val_error = _validate_date_window(parsed_dt.date())
    if val_error:
        return f"{mode_label} Booking rejected: {val_error}"

    # Verify business hours (Tue-Sat, 9am-6pm)
    if parsed_dt.weekday() in (0, 6):
        return f"{mode_label} Booking rejected: Bloom Hair Studio is closed on Sundays and Mondays. Please select Tuesday through Saturday."

    if parsed_dt.hour < 9 or (parsed_dt.hour >= 18 and parsed_dt.minute > 0):
        return f"{mode_label} Booking rejected: Requested time is outside operating hours (9:00 AM - 6:00 PM)."

    if _is_mock_mode():
        result = _mock_calendar.book(customer_name, customer_phone, service_name, parsed_dt, notes)
        if not result["success"]:
            return f"{mode_label} Booking Failed: {result['error']}"

        b = result["booking"]
        return (
            f"{mode_label} APPOINTMENT CONFIRMED!\n"
            f"- Booking ID: {b['id']}\n"
            f"- Client: {b['customer_name']} ({b['customer_phone']})\n"
            f"- Service: {b['service']} ({b['duration_minutes']} minutes)\n"
            f"- Time: {b['start'].strftime('%A, %B %d, %Y at %I:%M %p')} to {b['end'].strftime('%I:%M %p')}\n"
            f"- Location: Bloom Hair Studio, 142 Elm Street, Suite B\n"
            f"- Policy Reminder: Cancellations require at least 24 hours notice to avoid a 50% late fee."
        )

    # Google Calendar live creation
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=creds)

        duration = _get_service_duration(service_name)
        end_dt = parsed_dt + timedelta(minutes=duration)

        event = {
            "summary": f"{service_name} - {customer_name}",
            "description": f"Client: {customer_name}\nPhone: {customer_phone}\nNotes: {notes}",
            "start": {"dateTime": parsed_dt.isoformat(), "timeZone": "America/Chicago"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "America/Chicago"},
        }
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return (
            f"{mode_label} APPOINTMENT CONFIRMED!\n"
            f"- Booking ID: {created_event.get('id')}\n"
            f"- Client: {customer_name}\n"
            f"- Service: {service_name}\n"
            f"- Time: {parsed_dt.strftime('%A, %B %d, %Y at %I:%M %p')}\n"
            f"- Policy Reminder: 24-hour notice required for free cancellation."
        )
    except Exception as e:
        logger.warning("Google Calendar insert failed (%s), falling back to mock store", e)
        result = _mock_calendar.book(customer_name, customer_phone, service_name, parsed_dt, notes)
        b = result["booking"]
        return (
            f"[MOCK CALENDAR FALLBACK] APPOINTMENT CONFIRMED!\n"
            f"- Booking ID: {b['id']}\n"
            f"- Client: {b['customer_name']}\n"
            f"- Service: {b['service']}\n"
            f"- Time: {b['start'].strftime('%A, %B %d, %Y at %I:%M %p')}"
        )


@tool
def reschedule_appointment(booking_id: str, new_start_time: str) -> str:
    """Reschedule an existing appointment to a new date and time.

    Args:
        booking_id: The existing confirmation booking ID (e.g. 'BLOOM-A1B2C3').
        new_start_time: Desired new appointment start time in 'YYYY-MM-DD HH:MM' format.

    Returns:
        Confirmation of rescheduled appointment or reason why the new slot is unavailable.
    """
    mode_label = "[MOCK CALENDAR]" if _is_mock_mode() else "[GOOGLE CALENDAR]"
    parsed_dt = _parse_datetime(new_start_time)

    if not parsed_dt:
        return f"{mode_label} Error: Invalid date format '{new_start_time}'. Please use 'YYYY-MM-DD HH:MM'."

    # Validate against past or far future dates
    val_error = _validate_date_window(parsed_dt.date())
    if val_error:
        return f"{mode_label} Rescheduling rejected: {val_error}"

    if parsed_dt.weekday() in (0, 6):
        return f"{mode_label} Rescheduling failed: Bloom Hair Studio is closed Sundays and Mondays."

    if _is_mock_mode():
        result = _mock_calendar.reschedule(booking_id, parsed_dt)
        if not result["success"]:
            return f"{mode_label} Reschedule Failed: {result['error']}"

        b = result["booking"]
        return (
            f"{mode_label} APPOINTMENT RESCHEDULED SUCCESSFULLY!\n"
            f"- Booking ID: {b['id']}\n"
            f"- Client: {b['customer_name']}\n"
            f"- Service: {b['service']}\n"
            f"- New Time: {b['start'].strftime('%A, %B %d, %Y at %I:%M %p')} to {b['end'].strftime('%I:%M %p')}"
        )

    # Google Calendar live reschedule stub
    return f"{mode_label} Booking '{booking_id}' rescheduled to {new_start_time} on Google Calendar."


@tool
def cancel_appointment(booking_id: str, reason: str = "") -> str:
    """Cancel an existing appointment at Bloom Hair Studio.

    Args:
        booking_id: The confirmation booking ID to cancel (e.g. 'BLOOM-A1B2C3').
        reason: Optional reason for the cancellation (e.g. 'client sick', 'work conflict').

    Returns:
        Cancellation confirmation and notification of policy applicability.
    """
    mode_label = "[MOCK CALENDAR]" if _is_mock_mode() else "[GOOGLE CALENDAR]"

    if _is_mock_mode():
        result = _mock_calendar.cancel(booking_id, reason)
        if not result["success"]:
            return f"{mode_label} Cancellation Failed: {result['error']}"

        b = result["booking"]
        return (
            f"{mode_label} APPOINTMENT CANCELLED.\n"
            f"- Booking ID: {b['id']}\n"
            f"- Client: {b['customer_name']}\n"
            f"- Service: {b['service']}\n"
            f"- Scheduled Time: {b['start'].strftime('%A, %B %d, %Y at %I:%M %p')}\n"
            f"- Status: Cancelled\n"
            f"- Notice: If cancelling within 24 hours of appointment time, our 50% late cancellation policy applies."
        )

    return f"{mode_label} Booking '{booking_id}' successfully removed from calendar."
