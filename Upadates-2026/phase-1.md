Phase 1: Implementation Plan (Antigravity Orchestration)
Step 1: The "Governance Metadata" Refactor
Agent Mission: "Agent, your mission is to perform a project-wide refactor to remove all references to 'Software Autonomy' or 'Autonomous AI.' Update the system's core configuration to reflect a 'Clinician-Authorized' model. Provide a Walkthrough Artifact comparing the old autonomous logic with the new human-in-the-loop (HITL) architecture."

Workflow: Use Fast Mode for file-wide string replacements.

Target Files: Core prompt templates, A2UI JSON protocols, and README/Documentation files.

Key Constraint: Ensure no PHI is logged during the replacement process.

Step 2: Hard-Coding the Clinical Gate (Firestore & Security)
Agent Mission: "Agent, architect the Firestore schema to enforce a mandatory clinician sign-off. Create a Code Diff Artifact showing the new governance object and the updated Firestore Security Rules that block final intake processing until a clinician_signature_id is present."

Workflow: Use Planning Mode to ensure the security rules are bulletproof.

Antigravity Tooling: Use the Terminal to deploy the updated rules once the Artifact is reviewed.

Step 3: Visual Compliance via A2UI
Agent Mission: "Agent, update the A2UI (Sphere) protocol. The Sphere must now clearly indicate its status: 'Assisting' vs. 'Pending Clinician Review.' Ensure the patient-facing UI copy includes the mandatory AI disclosure. Use the Browser Agent to record a session showing the new disclosure."

Workflow: Browser Agent for verification.

Artifact: Browser Recording Artifact showing the "Talk to a Human" button is always persistent.

Antigravity "Mission Control" Setup
To begin, please follow this orchestration step:

Open the Agent Manager (Mission Control).

Paste the Mission from Step 1 (The Nomenclature Refactor).

Review the resulting Walkthrough Artifact here in our chat to confirm the "Autonomy" red flags are gone before we commit the code.

