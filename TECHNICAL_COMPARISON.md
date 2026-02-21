# The Intaker: Technical Comparison (Real Implementation vs. Promo Demo)

This document outlines the architectural and technical differences between the **Real Implementation** (Production Backend) and the **Promo Demo Version** (Browser-Native Simulation) of the Sphere UI.

---

## 1. Executive Summary

| Feature | Real Implementation (Production) | Promo Demo Version (Marketing/Wix) |
| :--- | :--- | :--- |
| **Primary Goal** | Clinical Intake, Logic & Treatment Planning | High-Fidelity Visuals & Scripted Walkthrough |
| **Voice Intelligence** | **Gemini Live API** (Multimodal LLM) | **Scripted State Machine** (Hardcoded) |
| **Speech Generation** | **Gemini 2.5 Flash** (Human-like, S2S) | **Web Speech API** (Standard TTS) |
| **Connectivity** | WebSocket (`wss://`) to Cloud Run | Offline / Client-Side Only (`window.*`) |
| **Logic Engine** | Python Backend (`services/voice-bridge`) | TypeScript Hook (`useVoiceBridge.ts`) |
| **Data Storage** | Firestore (HIPAA Compliant) | Ephmeral (In-Memory React State) |

---

## 2. Real Implementation (Production Structure)

The "Real" version is a fully functional, HIPAA-compliant microservices architecture designed to conduct actual clinical assessments.

### **Architecture**
*   **Frontend:** React (Vite) + Three.js (R3F)
    *   Located in: `frontend/src`
    *   Visuals: Displays real-time audio reactivity based on WebSocket stream amplitude.
*   **Backend:** Python FastAPI on Google Cloud Run
    *   Located in: `services/voice-bridge`
    *   **Orchestrator:** `main.py` handles WebSocket connections.
    *   **Auth:** Firebase Admin SDK (ID Token Verification).

### **Key Components**
1.  **Voice Bridge Service (`services/voice-bridge`)**:
    *   Acts as a secure proxy between the Client and Google's Gemini Live API.
    *   Handles "Server-to-Server" (S2S) audio streaming to protect API keys.
    *   **Tools:** Can call `finalize_intake()` tool to trigger scoring.
2.  **Scoring Engine (`services/scoring-engine`)**:
    *   Deterministic Python module that maps transcript text to ASAM Dimensions (1-6).
    *   Calculates Risk Ratings (0-4) based on clinical keywords.
3.  **Treatment Planner (`services/treatment_planner`)**:
    *   Generates a clinical narrative and "Level of Care" recommendation (e.g., Level 2.1 IOP) based on the calculated scores.

### **Latency & Network**
*   **Protocol:** Bi-directional WebSocket (`/ws/intake`).
*   **Latency:** ~600-900ms (Round trip Audio -> Cloud Run -> Gemini -> Cloud Run -> Audio).
*   **Security:** End-to-End Encryption, BAA-covered services.

---

## 3. Promo Demo Version (Wix Integration)

The "Promo" version is a **high-performance visual simulation** designed for marketing videos and website embedding (Wix). It removes all backend dependencies to ensure zero-latency demos and 100% uptime without server costs.

### **Architecture**
*   **Frontend:** React (Vite) + Three.js (R3F)
    *   Located in: `WIX-SPHERE-UI`
    *   **Bundle:** Compiles to a single `the-sphere-bundle.js` for embedding via `<custom-element>`.
*   **Backend:** **None** (Serverless/Static).

### **Key Components**
1.  **Browser-Native Voice Bridge (`src/hooks/useVoiceBridge.ts`)**:
    *   **Replaces** the WebSocket connection with browser APIs.
    *   **Listening:** Uses `webkitSpeechRecognition` (Chrome Native).
    *   **Speaking:** Uses `window.speechSynthesis` (OS Native Voices).
2.  **Ambassador Logic (Mode 7.0)**:
    *   A dual-mode "Brain" implemented entirely in TypeScript:
        *   **Ambassador Mode:** Recognizes keywords (`"Accreditation"`, `"AI"`, `"Telehealth"`) to deliver pre-written sales pitches.
        *   **Intake Mode:** A strict **"Scripted State Machine"**. It follows a linear array of questions (Speaker 2 transcript) regardless of user input, ensuring a perfect "Take 1" for video recording.
3.  **Visual Overrides**:
    *   **Background:** Transparent/White to blend with Wix sections.
    *   **Reactivity:** Simulates audio waves using simulated sine waves rather than real audio analysis (to prevent microphone permission friction).

---

## 4. Why Two Versions?

| Requirement | Solution | Reason |
| :--- | :--- | :--- |
| **HIPAA Compliance** | **Real Implementation** | Must store data securely, authorize users, and use private LLM instances. |
| **Video Production** | **Promo Version** | Need guaranteed responses (no hallucinations), zero network lag, and instant "Retry" capability. |
| **Wix Embedding** | **Promo Version** | Wix `<iframe>` limits microphone access and WebSocket stability; Client-side logic is more robust for public visitors. |
| **Clinical Accuracy** | **Real Implementation** | Requires the full Reasoning Model (Gemini) to assess complex patient histories. |

## 5. Development Workflows

*   **To edit the Real App:** Work in `frontend/` and `services/`. Run via `docker-compose` or `uvicorn`.
*   **To edit the Promo App:** Work in `WIX-SPHERE-UI/`. Run via `npm run dev`. Deploy using `npx vercel deploy --prod`.
