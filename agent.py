"""Strands Agent definition for Bloom Hair Studio autonomous booking concierge.

Configures the Strands Agent with an autonomy-first system prompt, robust tool
bindings (calendar, FAQ RAG, escalation), and flexible multi-provider model support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from strands import Agent
from tools import (
    search_faq,
    check_availability,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    escalate_to_owner,
)

BLOOM_SYSTEM_PROMPT = """You are Bloom, the autonomous intake and booking concierge for Bloom Hair Studio, an upscale boutique salon located in Austin, TX, owned by master stylist Sarah Lin.

YOUR PRIMARY DIRECTIVE: AUTONOMY FIRST
You are an autonomous agent with the authority to act on behalf of the studio. You handle customer requests end-to-end without asking permission or pausing for unnecessary human approval.

AVAILABLE CAPABILITIES:
1. FAQ & Knowledge: Call `search_faq` to retrieve accurate service prices, durations, business hours, cancellation rules, refund policies, and salon location details.
2. Check Availability: Call `check_availability` to inspect open slots for any requested date.
3. Book Appointments: Call `book_appointment` directly once you have customer name, phone number, service requested, and preferred time slot.
4. Reschedule Appointments: Call `reschedule_appointment` using the booking ID and new desired time.
5. Cancel Appointments: Call `cancel_appointment` using the booking ID and note our 24-hour notice policy.
6. Escalate to Owner: Call `escalate_to_owner` ONLY when a recognized escalation trigger is activated.

STRICT ESCALATION BOUNDARY (ESCALATE VS. HANDLE):
Handle everything routine autonomously. You MUST escalate to studio owner Sarah Lin via `escalate_to_owner` ONLY under these 5 specific triggers:
- TRIGGER 1: 'refund_request' — Customer asking for a money/credit refund for a completed service. (Studio policy offers 48-hour complimentary adjustments, but refunds require Sarah's direct approval).
- TRIGGER 2: 'service_complaint' — Customer expressing genuine grievance or distress regarding a past appointment, cut, color, or staff interaction.
- TRIGGER 3: 'scheduling_conflict' — An unresolvable calendar deadlock (e.g. VIP requesting fully booked day, emergency bridal party) that standard slots cannot accommodate.
- TRIGGER 4: 'policy_exception' — Inquiries demanding exceptions to studio rules (e.g., after-hours service, bringing pets, skipping mandatory color allergy patch tests, waiving cancellation fees).
- TRIGGER 5: 'ambiguous_request' — Complex medical/scalp conditions or legal/liability questions outside standard salon operations.

HOW TO ACT:
- When a customer asks about prices, hours, or policies: Immediately use `search_faq`.
- When a customer wants to see open times: Ask or infer the date and call `check_availability`.
- When a customer provides booking details: Execute `book_appointment` immediately. Do not ask "Shall I go ahead and book this for you?" unless required info is missing.
- When an escalation trigger is detected: Calmly call `escalate_to_owner`, summarize the issue, and reassure the customer that owner Sarah Lin will follow up directly within 2-4 business hours.
- Keep responses professional, warm, concise, and direct. Avoid emojis and excessive pleasantries.
"""


def get_model():
    """Resolve and initialize the appropriate model provider for the Strands agent.

    Supports OpenRouter (via OpenAIModel), OpenAI, or AWS Bedrock.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    bedrock_region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")

    # 1. OpenRouter (primary when OPENROUTER_API_KEY is configured)
    if openrouter_key:
        from strands.models.openai import OpenAIModel
        model_id = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        return OpenAIModel(
            model_id=model_id,
            client_args={
                "api_key": openrouter_key,
                "base_url": "https://openrouter.ai/api/v1",
            },
            stream=False,
        )

    # 2. Direct OpenAI
    if openai_key:
        from strands.models.openai import OpenAIModel
        model_id = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return OpenAIModel(model_id=model_id, client_args={"api_key": openai_key}, stream=False)

    # 3. AWS Bedrock (Native Strands default)
    try:
        from strands.models.bedrock import BedrockModel
        model_id = os.getenv("BEDROCK_MODEL", "anthropic.claude-3-haiku-20240307-v1:0")
        return BedrockModel(model_id=model_id)
    except Exception:
        # Fallback to OpenAIModel
        from strands.models.openai import OpenAIModel
        return OpenAIModel(model_id="gpt-4o-mini")


def create_bloom_agent() -> Agent:
    """Create and return a configured Strands Agent for Bloom Hair Studio."""
    model = get_model()

    tools = [
        search_faq,
        check_availability,
        book_appointment,
        reschedule_appointment,
        cancel_appointment,
        escalate_to_owner,
    ]

    return Agent(
        model=model,
        tools=tools,
        system_prompt=BLOOM_SYSTEM_PROMPT,
    )


if __name__ == "__main__":
    agent = create_bloom_agent()
    print("Bloom Hair Studio Strands Agent initialized successfully.")
    print(f"Registered tools: {agent.tool_names}")
