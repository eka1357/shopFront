# shopfront-agent: Autonomous Intake & Booking Concierge

**Built for the AWS "Agents for Humans" Hackathon — Professional Agents Track**  
*Showcasing real-world autonomy using the AWS Strands Agents SDK*

---

## What It Does
**shopfront-agent** is an autonomous intake and scheduling agent deployed for small service businesses, demonstrated through a boutique salon (**Bloom Hair Studio**, Austin, TX).

Unlike conventional conversational bots that merely chat about scheduling or constantly ask "Would you like me to book this for you?", **shopfront-agent operates on an autonomy-first model**:
- **Answers Business FAQs Instantly**: Uses local TF-IDF semantic retrieval over `faq.md` for pricing, service durations, cancellation terms, and parking rules without calling external vector databases.
- **Inspects Real Calendar Availability**: Queries open slots in real-time while respecting business hours (Tuesday–Saturday, 9:00 AM – 6:00 PM) and filtering out conflicts.
- **Acts End-to-End**: Autonomously creates, reschedules, and cancels appointments directly on the calendar.
- **Judiciously Escalates**: Detects named edge-case triggers (refund demands, unhappy clients, schedule collisions, policy overrides) and routes structured escalation tickets to studio owner Sarah Lin via `escalations.json` while calming and reassuring the client.

---

## Who It Is For
Small service business owners (hair salons, wellness clinics, massage studios, boutique fitness, and solo professionals) who lose hours every day answering repetitive scheduling messages, handling no-shows, and manually rescheduling clients.

---

## Why It Matters
Independent service operators spend up to 15 hours a week playing telephone tag over text messages and Instagram DMs to coordinate bookings. Most AI scheduling demos are shallow wrappers that fail when a client asks for a refund, requests an off-hours slot, or tries to double-book a busy time.

**shopfront-agent demonstrates that an agent built with the AWS Strands Agents SDK can be truly autonomous**:
1. It takes decisive action on routine tasks without human micromanagement.
2. It respects business policy boundaries without breaking.
3. It knows exactly when and how to escalate to human owners with full context.

---

## Architecture & Decision Flow

See [architecture.md](architecture.md) for complete component topology, sequence diagrams, and entity schemas.

```
+-------------------------------------------------------------------+
|                        Customer (CLI / Chat)                      |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|               AWS Strands Agent Core (agent.py)                   |
|           Autonomy-First System Prompt & ReAct Event Loop         |
+-------------------------------------------------------------------+
         |                        |                        |
         v                        v                        v
+-----------------+      +-----------------+      +-----------------+
|  tools/faq_tool |      | tools/calendar  |      | tools/escalate  |
| Local TF-IDF    |      | Dual-Engine:    |      | Named Triggers  |
| RAG over        |      | Google API /    |      | & Atomic Log    |
| faq.md          |      | In-Memory Mock  |      | escalations.json|
+-----------------+      +-----------------+      +-----------------+
```

---

## Escalation Logic: How the Agent Decides

The agent is instructed to handle all routine requests autonomously. Escalation is an **exception path** triggered only when one of five named triggers occurs:

| Named Trigger | Scenario | Agent Action |
| :--- | :--- | :--- |
| `refund_request` | Client unhappy with service and demands cash refund | Queries refund policy (no cash refunds; 48-hr complimentary adjustment), logs high-urgency ticket to `escalations.json`, and arranges direct owner follow-up. |
| `service_complaint` | Client reporting damaged hair or poor stylist interaction | Acknowledges concern calmly, creates tracked escalation ticket, and routes to owner for personal handling. |
| `scheduling_conflict` | Unresolvable calendar collision or emergency VIP booking | Identifies impossible constraint, logs conflict details, and alerts owner to manually adjust schedule. |
| `policy_exception` | Request for off-hours appointment (e.g. Sunday) or skipping chemical patch test | Explains studio rule and escalates to owner if client insists on an executive exception. |
| `ambiguous_request` | High-liability medical/scalp concerns or legal queries | Refrains from guessing and transfers intake to owner discretion. |

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- Virtual environment tool (`venv`)

### 2. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/eka1357/shopFront.git
cd shopFront

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate

# Install dependencies (installs in under 2 minutes)
pip install -r requirements.txt
```

### 3. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Provide your API key (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, or AWS Bedrock credentials).

> **Zero-Credential Demo Mode**: By default, `MOCK_CALENDAR=true` is enabled. The calendar runs an in-memory store pre-populated with realistic bookings and business hours, so no Google Cloud credentials are required to test or evaluate the demo.

### 4. Run the Agent
```bash
python main.py
```

---

## Verification & Testing

To run the automated end-to-end verification suite:
```bash
python test_agent.py
```

This validates:
1. FAQ semantic search accuracy over prices, hours, and policies.
2. Calendar availability, conflict detection, booking, rescheduling, and cancellation.
3. Owner escalation logging and persistence in `escalations.json`.
4. Multi-turn autonomous dialogue through the Strands Agent loop.

---

## License
Distributed under the [MIT License](LICENSE).
