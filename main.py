"""Interactive CLI chat loop for Bloom Hair Studio autonomous booking concierge.

Built for the AWS 'Agents for Humans' Hackathon (Professional Agents Track).
Provides a streamlined terminal interface to test autonomous scheduling,
FAQ retrieval, and escalation boundaries end-to-end.
"""

import os
import sys
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

from agent import create_bloom_agent
from strands.handlers import null_callback_handler
from tools.calendar_tool import _is_mock_mode


def print_banner(mock_active: bool) -> None:
    """Print clean, branded terminal header following hackathon design guidelines."""
    calendar_status = "Mock Calendar Active (In-Memory)" if mock_active else "Google Calendar Connected"
    
    print("\n" + "=" * 64)
    print("BLOOM HAIR STUDIO -- AUTONOMOUS BOOKING CONCIERGE")
    print("Austin, TX | Master Stylist: Sarah Lin")
    print("Powered by AWS Strands Agents SDK")
    print(f"Calendar Mode: {calendar_status}")
    print("=" * 64)
    print("Type your message below to book, reschedule, or ask questions.")
    print("Type 'exit' to quit or 'reset' to start a new conversation.\n")


def run_chat_loop() -> None:
    """Run interactive conversation loop with Strands Agent."""
    mock_active = _is_mock_mode()
    print_banner(mock_active)

    print("Initializing Strands Agent...")
    try:
        # Disable default streaming callback handler to prevent duplicate printing in CLI demo
        agent = create_bloom_agent(callback_handler=null_callback_handler)
        print("Concierge ready.\n")
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("Customer: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSession ended. Thank you for visiting Bloom Hair Studio.")
            break

        if not user_input:
            continue

        command = user_input.lower()
        if command in ("exit", "quit", "q"):
            print("\nSession ended. Thank you for visiting Bloom Hair Studio.")
            break

        if command == "reset":
            print("\nResetting concierge conversation state...")
            agent = create_bloom_agent(callback_handler=null_callback_handler)
            print("Conversation reset. How can Bloom Hair Studio help you today?\n")
            continue

        try:
            result = agent(user_input)
            response_text = ""

            if hasattr(result, "message") and isinstance(result.message, dict):
                content = result.message.get("content", [])
                if isinstance(content, list):
                    texts = [c.get("text", "") for c in content if isinstance(c, dict) and "text" in c]
                    response_text = "\n".join(texts).strip()
                elif isinstance(content, str):
                    response_text = content.strip()

            if not response_text and hasattr(result, "text"):
                response_text = str(result.text).strip()

            if not response_text:
                response_text = str(result)

            print(f"\nBloom: {response_text}\n")

        except Exception as err:
            print(f"\nSystem Error: {err}\n")


if __name__ == "__main__":
    run_chat_loop()
