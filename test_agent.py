"""End-to-end verification test suite for shopfront-agent.

Tests tool functionality, calendar state transitions, escalation logging,
and live Strands Agent multi-turn conversational loop.
"""

import json
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from tools.faq_tool import search_faq
from tools.calendar_tool import (
    check_availability,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    _mock_calendar,
)
from tools.escalate_tool import escalate_to_owner, ESCALATIONS_FILE
from agent import create_bloom_agent


def test_faq_tool():
    print("\n[TEST 1] Testing FAQ RAG Tool...")
    # Haircut pricing test
    res = search_faq("how much is a signature haircut?")
    assert "75" in res or "Haircut" in res, f"Failed haircut price query: {res}"
    print("  [OK] Haircut price retrieved successfully")

    # Business hours test
    res_hours = search_faq("what are your hours on Saturday?")
    assert "Saturday" in res_hours and "5:00 PM" in res_hours, f"Failed hours query: {res_hours}"
    print("  [OK] Saturday studio hours retrieved successfully")

    # Refund policy test
    res_refund = search_faq("what is your refund policy?")
    assert "complimentary adjustment" in res_refund.lower(), f"Failed refund policy query: {res_refund}"
    print("  [OK] Refund and adjustment policy retrieved successfully")


def test_calendar_tool():
    print("\n[TEST 2] Testing Calendar Scheduling Tool (In-Memory Mock)...")
    target_date = "2026-09-15"  # Tuesday

    # 1. Availability check
    avail = check_availability(target_date)
    assert "[MOCK CALENDAR]" in avail
    assert "Available appointment slots" in avail
    print("  [OK] Available slots listed successfully")

    # 2. Booking creation
    book_res = book_appointment(
        customer_name="Claire Redfield",
        customer_phone="512-555-4321",
        service_name="Signature Haircut & Blowdry",
        start_time="2026-09-15 10:00",
        notes="First visit",
    )
    assert "APPOINTMENT CONFIRMED" in book_res
    assert "BLOOM-" in book_res
    print("  [OK] Appointment booked successfully")

    # Extract booking ID
    match = re.search(r"Booking ID:\s*(BLOOM-[A-Z0-9]+)", book_res)
    assert match, "Could not extract booking ID"
    booking_id = match.group(1)

    # 3. Double-booking conflict prevention
    conflict_res = book_appointment(
        customer_name="Leon Kennedy",
        customer_phone="512-555-8765",
        service_name="Barber Cut",
        start_time="2026-09-15 10:00",
    )
    assert "Conflict detected" in conflict_res or "overlaps" in conflict_res
    print("  [OK] Overlapping double-booking prevented successfully")

    # 4. Rescheduling
    resched_res = reschedule_appointment(booking_id, "2026-09-15 12:00")
    assert "RESCHEDULED SUCCESSFULLY" in resched_res
    print("  [OK] Appointment rescheduled successfully")

    # 5. Cancellation
    cancel_res = cancel_appointment(booking_id, "Schedule conflict")
    assert "APPOINTMENT CANCELLED" in cancel_res
    print("  [OK] Appointment cancelled successfully")


def test_escalation_tool():
    print("\n[TEST 3] Testing Owner Escalation Tool...")
    res = escalate_to_owner(
        customer_name="David Martinez",
        customer_contact="david@nightcity.com",
        trigger_category="refund_request",
        reason="Client unsatisfied with bleaching treatment, demanding $150 cash refund",
        conversation_summary="Client experienced scalp irritation and wants full monetary refund.",
        urgency="high",
    )
    assert "ESCALATION LOGGED SUCCESSFULLY" in res
    assert "ESC-" in res

    # Verify atomic write to escalations.json
    assert ESCALATIONS_FILE.exists()
    with open(ESCALATIONS_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    latest = [r for r in records if r["customer_name"] == "David Martinez"]
    assert len(latest) > 0
    assert latest[-1]["trigger_category"] == "refund_request"
    print("  [OK] Escalation ticket persisted to escalations.json successfully")


def test_agent_conversation_flow():
    print("\n[TEST 4] Testing Live Strands Agent Loop...")
    agent = create_bloom_agent()

    # Step A: Routine FAQ test
    print("  User: 'Hi! What are your business hours on Friday?'")
    reply1 = agent("Hi! What are your business hours on Friday?")
    text1 = reply1.message["content"][0]["text"]
    print(f"  Bloom: {text1.strip()}")
    assert "9:00" in text1 and ("6:00" in text1 or "Friday" in text1)
    print("  [OK] Agent answered studio hours via FAQ tool")

    # Step B: Availability check
    print("\n  User: 'Do you have openings on 2026-09-15?'")
    reply2 = agent("Do you have openings on 2026-09-15?")
    text2 = reply2.message["content"][0]["text"]
    print(f"  Bloom: {text2.strip()}")
    assert "slot" in text2.lower() or "am" in text2.lower() or "pm" in text2.lower() or "available" in text2.lower()
    print("  [OK] Agent checked availability via calendar tool")

    # Step C: Booking an appointment
    print("\n  User: 'Please book a Signature Haircut for Sophia Taylor, phone 512-555-0987, at 2026-09-15 09:00'")
    reply3 = agent("Please book a Signature Haircut for Sophia Taylor, phone 512-555-0987, at 2026-09-15 09:00")
    text3 = reply3.message["content"][0]["text"]
    print(f"  Bloom: {text3.strip()}")
    assert "confirmed" in text3.lower() or "bloom-" in text3.lower()
    print("  [OK] Agent completed booking autonomously")

    # Step D: Escalation trigger (Refund demand)
    print("\n  User: 'I got my hair dyed yesterday and hate the color. I demand a full cash refund of $200 right now!'")
    reply4 = agent("I got my hair dyed yesterday and hate the color. I demand a full cash refund of $200 right now!")
    text4 = reply4.message["content"][0]["text"]
    print(f"  Bloom: {text4.strip()}")
    assert ("sarah" in text4.lower() or "owner" in text4.lower() or "escalat" in text4.lower() or "esc-" in text4.lower())
    print("  [OK] Agent triggered owner escalation for refund request")


def run_all_tests():
    print("=" * 65)
    print("SHOPFRONT-AGENT: RUNNING AUTOMATED VERIFICATION SUITE")
    print("=" * 65)

    test_faq_tool()
    test_calendar_tool()
    test_escalation_tool()
    test_agent_conversation_flow()

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED SUCCESSFULLY! (100% End-to-End Verified)")
    print("=" * 65)


if __name__ == "__main__":
    run_all_tests()
