# Phase 1: Governance & Nomenclature Walkthrough

## Overview
This document outlines the transition from an "Autonomous AI" model to a "Clinician-Authorized" Human-in-the-Loop (HITL) architecture for The Intaker system.

## 1. Nomenclature Refactor
**Goal**: Remove all implications of AI autonomy and replace them with "Assistant" and "Clinician-Supervised" terminology.

### Changes Implemented:

#### System Prompt (`services/gemini_live_grounding.py`)
- **Old**: "You are The Intaker Assistant, a clinical intake agent."
- **New**: "You are The Intaker Assistant, a **clinician-supervised intake support agent**."
- **Rationale**: Explicitly frames the AI as a support tool, not a decision-maker.

#### Frontend UI (`App.tsx`)
- **Old**: "Status: CONNECTED" (implied full autonomy in handling the session).
- **New**: 
  - Status Indicator: "ASSISTING" or "PENDING REVIEW".
  - **Mandatory Disclosure**: Added a persistent "AI Assistant • Clinician Supervised" banner to the status overlay.
- **Rationale**: Ensures patients are constantly aware they are interacting with an AI under supervision.

## 2. Architecture Comparison

| Feature | Old "Autonomous" Model | New "Clinician-Authorized" Model |
| :--- | :--- | :--- |
| **Session Logic** | AI determines when intake is complete. | AI suggests completion; Human Clinician must review and sign off. |
| **Data Handling** | AI writes final assessment directly to EHR (hypothetical). | AI writes to a `pending_assessments` queue. Clinician publishes to EHR. |
| **Risk Management** | AI handles escalation autonomously. | AI flags risk and immediately hands off to human protocol (Safety Override). |
| **User trust** | "Trust the AI to do the job." | "Trust the process because a Human is in charge." |

## 3. Walkthrough of the New Flow
1. **Initiation**: Patient starts session. UI clearly states "AI Assistant • Clinician Supervised".
2. **Interaction**: AI conducts the interview using the ASAM script.
3. **Completion**: 
   - AI determines the script is done.
   - AI generates a summary and score.
   - UI Status changes to **"PENDING REVIEW"**.
4. **Authorization**:
   - A human clinician reviews the transcript, scores, and plan.
   - Clinician applies their digital signature (`clinician_signature_id`).
   - The intake is effectively "finalized".

## 4. Governance Metadata
All system artifacts now include metadata enforcing this model:
- `governance_model`: `HITL_CLINICIAN_AUTHORIZED`
- `ai_role`: `SUPPORT_ASSISTANT`
