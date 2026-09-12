# AGENTS.md — shopfront-agent (Agents for Humans Hackathon)

## Context
Building a Strands Agents SDK project for AWS's "Agents for Humans" hackathon,
Professional Agents track. Submission deadline Sep 15, 5:30am IST. Two-day build.
This file is the standing spec — follow it for every task in this repo, not just
the first scaffold.

## What we're building
An autonomous booking and intake agent for a small service business ("Bloom Hair
Studio"). It books, reschedules, and cancels appointments, answers FAQs, and only
escalates to the human owner when something is genuinely ambiguous. The judged bar
is: does it act end-to-end on its own, not just chat about acting.

## Tech stack (do not substitute without asking)
- Python 3.11+
- AWS Strands Agents SDK — use its agent + tools pattern, not a raw LLM call wrapped
  in if/else logic
- Google Calendar API for real scheduling, with a MOCK_CALENDAR=true in-memory
  fallback so the demo never depends on live credentials
- Local RAG for FAQs (sentence-transformers if it installs quickly, otherwise a
  TF-IDF fallback) — no external vector DB, this needs to run in one command
- ElevenLabs for voice, added only after the text version fully works — never let
  voice integration block the core agent logic

## Non-negotiable build rules
1. The agent must reason about escalate-vs-handle, not default to asking permission
   for everything. Write the system prompt so autonomy is the default and
   escalation is the exception, with named triggers (refund/complaint, conflicting
   booking it can't resolve, anything outside the business's stated policies).
2. Every tool call must be a real Strands tool, not a mocked string return pretending
   to be one, except the calendar mock mode, which must be clearly labeled as mock.
3. No secrets in code or in anything committed. All credentials go through .env,
   and .env.example lists every variable with a one-line comment, no real values.
4. Every feature must be run and verified working before it's considered done. If
   something can't be verified end-to-end in the time left, cut it, don't leave it
   half-wired.
5. Code must be readable by a judge skimming it once. Comment the why, not the what.
6. Don't add a feature that isn't in this file or asked for directly. Scope is fixed
   because time is fixed.

## Repo hygiene
- MIT license file, visible at repo root
- README.md must cover: what it does, who it's for, why it matters, setup steps,
  how the escalation logic works, and a link to the architecture diagram
- architecture.md describing agent, tools, and decision flow, for turning into a
  diagram
- No unused dependencies in requirements.txt
- No dead code, no commented-out blocks left in

## Design rules for any UI (demo dashboard, landing page, or video overlay)
These come from a known list of tells that make software look AI-generated. Treat
every item below as a hard rule, not a suggestion. If a design decision matches an
item on the left, it's rejected — pick the alternative instead or something more
specific to this product.

Reject: harsh gradients, lucide icons used generically, pure white background,
rainbow coloring, drop shadows on everything, three feature cards in a row, emojis
as UI elements, liquid glass effects, em dashes in copy, default Inter/Geist/Space
Grotesk with no other typographic choice, a colored left stripe as a design motif,
fake testimonials, bento grid layouts, a fake terminal window as decoration, "it's
not X, it's Y" copywriting, checkmark bullet lists, three pricing tiers, no real
product demo on the page, soft/rounded corners everywhere, purple-and-black as the
palette, no skeleton loaders during data fetch, radial gradient orbs in the
background, dot grid backgrounds, sparkle icons, animated arrows, missing Terms of
Service, missing privacy policy, hover animations added for their own sake, neon
colors, basic pastel colors.

Instead: pick one deliberate color rooted in the actual brand (a hair studio, not
a generic SaaS palette), use real screenshots or a real recorded interaction
instead of mockups, write plain declarative copy, choose a typeface and layout that
looks like it was designed for this specific product, and if pricing or legal pages
aren't part of the actual submission requirement, leave them out rather than
faking them.

## What still needs to be decided before build starts
- Exact FAQ content for Bloom Hair Studio (services, hours, cancellation policy)
- Whether the demo video shows the CLI directly or a thin UI wrapper around it
- Whether Google Calendar OAuth is set up with real credentials or the mock mode
  is used for the whole demo (mock mode is safer given the timeline)

## Definition of done for the hackathon submission
- Agent runs end-to-end from a clean clone with one install command
- README, LICENSE, architecture.md, .env.example all present
- Repo is public with the license visible in the About section
- Demo video recorded, under 5 minutes, covers problem, audience, why it matters,
  and a live run of the agent
- AWS Builder ID linked in the submission
