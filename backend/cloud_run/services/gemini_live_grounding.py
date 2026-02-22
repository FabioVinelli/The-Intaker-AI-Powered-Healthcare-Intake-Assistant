"""
Gemini Live grounding utility for The Intaker (HIPAA-safe).

This module:
- Calls the GetActiveScript HTTP endpoint to retrieve the active ASAM script and components.
- Builds a strict "System Instruction" block that mandates adherence to the script.
- Provides a RAG-style "context supplement" / "declarative tool" payload that can be injected into
  a Gemini Live session configuration.
- Provides simple, conservative high-risk phrase detection to trigger escalation guidance
  (without logging user utterances).

This file intentionally does NOT call the Gemini API directly; it produces the inputs needed for
the integration layer that manages a Live session.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from xml.etree import ElementTree as ET

from backend.shared.logging_service import EventType, get_logger


logger = get_logger("gemini_live_grounding")


DEFAULT_SCRIPT_ID = os.getenv("DEFAULT_SCRIPT_ID", "full_asam_script_humanized")
GET_ACTIVE_SCRIPT_URL = os.getenv("GET_ACTIVE_SCRIPT_URL")  # e.g. https://REGION-PROJECT.cloudfunctions.net/get-active-script


class GetActiveScriptError(RuntimeError):
    pass


# -----------------------------------------------------------------------------
# Local testing mode: read directly from DOCX (bypasses HTTP call)
# -----------------------------------------------------------------------------

DOCX_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _extract_docx_text(docx_path: str) -> str:
    """Extract plain text from DOCX by reading word/document.xml."""
    with zipfile.ZipFile(docx_path) as z:
        xml_bytes = z.read("word/document.xml")
    root = ET.fromstring(xml_bytes)
    ns = {"w": DOCX_W_NS}
    paragraphs = []
    for p in root.findall(".//w:p", ns):
        texts = [t.text for t in p.findall(".//w:t", ns) if t.text]
        if texts:
            paragraphs.append("".join(texts))
    return "\n".join(paragraphs).strip()


def _try_json_loads_with_fixes(s: str) -> Optional[Dict[str, Any]]:
    """Try parsing JSON with small normalizations for Word artifacts."""
    candidates = [s]
    candidates.append(
        s.replace(""", '"')
        .replace(""", '"')
        .replace("'", "'")
        .replace("'", "'")
        .replace("\u00a0", " ")
    )
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


def fetch_active_script_from_docx(docx_path: str, script_id: Optional[str] = None) -> ActiveScript:
    """
    Fetch script data directly from DOCX file (local testing mode).
    
    This bypasses the HTTP call and reads the JSON directly from the DOCX,
    useful for testing before the Cloud Function is deployed.
    """
    if not os.path.exists(docx_path):
        raise GetActiveScriptError(f"DOCX file not found: {docx_path}")
    
    text = _extract_docx_text(docx_path)
    payload = _try_json_loads_with_fixes(text)
    
    if not payload or not isinstance(payload, dict):
        raise GetActiveScriptError("Could not parse JSON from DOCX file")
    
    version = str(payload.get("version") or "").strip()
    if not version:
        raise GetActiveScriptError("DOCX payload missing 'version' field")
    
    script_name = str(payload.get("script_name") or "").strip()
    description = str(payload.get("description") or "").strip()
    
    scoring_weights = payload.get("scoring_weights")
    escalation_protocols = payload.get("escalation_protocols")
    if not isinstance(scoring_weights, dict):
        raise GetActiveScriptError("DOCX payload missing 'scoring_weights' object")
    if not isinstance(escalation_protocols, dict):
        raise GetActiveScriptError("DOCX payload missing 'escalation_protocols' object")
    
    # "scriptData" = everything except top-level metadata + extracted components
    script_data = dict(payload)
    for k in ["version", "script_name", "description", "scoring_weights", "escalation_protocols"]:
        script_data.pop(k, None)
    
    sid = (script_id or DEFAULT_SCRIPT_ID).strip()
    
    logger.info(
        "Loaded script from DOCX (local mode)",
        event_type=EventType.API_REQUEST,
        script_id=sid,
        version=version,
        source_file=os.path.basename(docx_path),
    )
    
    return ActiveScript(
        script_id=sid,
        version=version,
        script_name=script_name,
        description=description,
        script_data=script_data,
        scoring_weights=scoring_weights,
        escalation_protocols=escalation_protocols,
    )


@dataclass(frozen=True)
class ActiveScript:
    script_id: str
    version: str
    script_name: Optional[str]
    description: Optional[str]
    script_data: Dict[str, Any]
    scoring_weights: Optional[Dict[str, Any]]
    escalation_protocols: Optional[Dict[str, Any]]


def _http_json_get(url: str, *, timeout_s: float) -> Tuple[int, Dict[str, Any]]:
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        status = int(getattr(resp, "status", 200))
        body = resp.read()
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception as e:
            raise GetActiveScriptError(f"Invalid JSON response: {e}") from e
        return status, data


def fetch_active_script(
    *,
    get_active_script_url: Optional[str] = None,
    script_id: Optional[str] = None,
    timeout_s: float = 10.0,
) -> ActiveScript:
    """
    Fetch the active intake script from the GetActiveScript endpoint.

    Security/HIPAA:
    - Logs only metadata (script_id, version, response size). Never logs script content.
    """
    base = (get_active_script_url or GET_ACTIVE_SCRIPT_URL or "").strip()
    if not base:
        raise GetActiveScriptError(
            "GET_ACTIVE_SCRIPT_URL is not set. Provide get_active_script_url=... or set env var GET_ACTIVE_SCRIPT_URL."
        )

    sid = (script_id or DEFAULT_SCRIPT_ID).strip()
    if not sid:
        raise GetActiveScriptError("script_id is empty")

    url = base
    # allow callers to pass either a bare endpoint or an existing URL with query
    if "?" in base:
        url = base
    else:
        url = f"{base}?{urllib.parse.urlencode({'script_id': sid})}"

    start = time.time()
    logger.info(
        "Fetching active script",
        event_type=EventType.API_REQUEST,
        script_id=sid,
        endpoint="get_active_script",
    )

    status, payload = _http_json_get(url, timeout_s=timeout_s)
    elapsed_ms = round((time.time() - start) * 1000, 2)

    if status != 200 or not isinstance(payload, dict) or not payload.get("ok"):
        logger.warning(
            "GetActiveScript returned error",
            event_type=EventType.API_ERROR,
            script_id=sid,
            status_code=status,
            duration_ms=elapsed_ms,
            error_code=(payload.get("error") or {}).get("code") if isinstance(payload, dict) else None,
        )
        raise GetActiveScriptError(f"GetActiveScript failed (status={status})")

    version = str(payload.get("version") or "").strip()
    data = payload.get("scriptData")
    if not version or not isinstance(data, dict):
        raise GetActiveScriptError("GetActiveScript response missing required fields: version/scriptData")

    components = payload.get("components") if isinstance(payload.get("components"), dict) else {}
    scoring_weights = components.get("scoring_weights") if isinstance(components.get("scoring_weights"), dict) else None
    escalation_protocols = (
        components.get("escalation_protocols") if isinstance(components.get("escalation_protocols"), dict) else None
    )

    logger.info(
        "Fetched active script metadata",
        event_type=EventType.API_RESPONSE,
        script_id=sid,
        version=version,
        duration_ms=elapsed_ms,
        has_scoring_weights=bool(scoring_weights),
        has_escalation_protocols=bool(escalation_protocols),
    )

    return ActiveScript(
        script_id=sid,
        version=version,
        script_name=payload.get("script_name"),
        description=payload.get("description"),
        script_data=data,
        scoring_weights=scoring_weights,
        escalation_protocols=escalation_protocols,
    )


# -----------------------------------------------------------------------------
# High-risk detection (conservative) + escalation guidance
# -----------------------------------------------------------------------------

_HIGH_RISK_PATTERNS = [
    r"\b(suicid(al|e)|kill\s+myself|end\s+my\s+life|want\s+to\s+die)\b",
    r"\b(self[-\s]?harm|hurt(ing)?\s+myself|cut(ting)?\s+myself)\b",
    r"\b(overdose|od\b|took\s+too\s+many|pills)\b",
    r"\b(abuse|hit\s+me|beat\s+me|hurt\s+me)\b",
]
_HIGH_RISK_RE = re.compile("|".join(_HIGH_RISK_PATTERNS), flags=re.IGNORECASE)


def contains_high_risk_symptom(user_text: str) -> bool:
    """
    Returns True if the text appears to mention high-risk symptoms.
    Do NOT log user_text (HIPAA).
    """
    if not user_text:
        return False
    return bool(_HIGH_RISK_RE.search(user_text))


def build_escalation_addendum(escalation_protocols: Optional[Dict[str, Any]]) -> str:
    """
    Builds a short, strict instruction chunk to force escalation handling when risk is detected.
    """
    proto_hint = ""
    if escalation_protocols:
        # Include a stronger reference.
        proto_hint = "CONSULT THE 'escalation_protocols' IN YOUR CONTEXT immediately."

    return (
        "!!! HIGH-RISK SAFETY OVERRIDE !!!\n"
        "You have detected a potential safety risk (suicide, self-harm, overdose, or violence).\n"
        "1. STOP the normal script flow IMMEDIATELY.\n"
        "2. ACKNOWLEDGE the user's distress with empathy, but DO NOT try to treat or solve it.\n"
        f"3. {proto_hint}\n"
        "4. Output the specific safety triage questions or handoff instructions required by the protocol.\n"
        "5. Do NOT return to the normal script until the safety risk is fully triaged and resolved per protocol.\n"
        "!!! END SAFETY OVERRIDE !!!\n"
    ).strip()


# -----------------------------------------------------------------------------
# Gemini Live inputs
# -----------------------------------------------------------------------------

def build_a2ui_instruction() -> str:
    """
    Returns the A2UI (Adaptive UI) protocol instructions.
    """
    return (
        "A2UI PROTOCOL (Adaptive UI Rendering):\n"
        "- Use this protocol when the script requires structured user input (ratings, multiple choice, forms).\n"
        "- FORMAT: Append a SINGLE <a2ui> JSON block at the very END of your text response.\n"
        "- Do NOT put the <a2ui> block in the middle of text. It must be suffix-only.\n"
        "- JSON SCHEMA:\n"
        "  <a2ui>\n"
        "  {\n"
        "    \"type\": \"slider\" | \"radio\" | \"checkbox\" | \"info\",\n"
        "    \"label\": \"<The exact question text>\",\n"
        "    \"min\": number, \"max\": number, \"step\": number (for slider),\n"
        "    \"options\": [{\"value\": \"v1\", \"label\": \"OD\"}, ...] (for radio/checkbox)\n"
        "  }\n"
        "  </a2ui>\n"
        "- EXAMPLES:\n"
        "  * Slider: <a2ui>{ \"type\": \"slider\", \"label\": \"Rate your pain (0-10)\", \"min\": 0, \"max\": 10, \"step\": 1 }</a2ui>\n"
        "  * Radio:  <a2ui>{ \"type\": \"radio\", \"label\": \"Select frequency\", \"options\": [\"Daily\", \"Weekly\", \"Rarely\"] }</a2ui>\n"
        "- NOTE: If the script node implies a multiple-choice question, YOU MUST use 'radio' or 'checkbox' type.\n"
        "- HANDLING USER SELECTIONS:\n"
        "  * The user's UI selection will be injected as a system message: '[A2UI Selection: <Label> = <Value>]'\n"
        "  * You MUST treat this as a definitive answer to the question.\n"
        "  * Use the value to evaluate the 'next_step' logic in the scriptData immediately.\n"
        "  * Do not ask the user to confirm the value. Proceed to the next step.\n"
    ).strip()


def build_declarative_context(active: ActiveScript) -> Dict[str, Any]:
    """
    Builds the declarative context object (RAG-like injection).
    """
    return {
        "type": "declarative_context",
        "name": "asam_intake_script",
        "schema_version": "1",
        "script_id": active.script_id,
        "version": active.version,
        "content": {
            "scriptData": active.script_data,
            "components": {
                "scoring_weights": active.scoring_weights,
                "escalation_protocols": active.escalation_protocols,
            },
        },
    }

def build_system_instruction(
    active: ActiveScript,
    start_at: Optional[str] = None,
    progress_history: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build a strict system instruction string.
    Keep it deterministic and policy-focused. Do not embed PHI.
    
    Args:
        active: The active script bundle.
        start_at: The node ID to resume/start at.
        progress_history: A dictionary of key-value pairs representing answers already collected.
    """
    header = (
        "You are The Intaker Assistant, a clinician-supervised intake support agent.\n"
        "You MUST follow the provided ASAM intake script exactly.\n"
        "Do NOT skip questions, do NOT invent new questions, and do NOT reorder steps unless the script logic requires it.\n"
        "If the user refuses or is unsure, follow the script's re-ask / clarification path.\n"
        "Maintain a calm, professional tone.\n"
        "Never request or store unnecessary identifying information.\n"
    )

    script_meta = (
        f"SCRIPT CONTEXT:\n"
        f"- script_id: {active.script_id}\n"
        f"- version: {active.version}\n"
        f"- script_name: {active.script_name or 'unknown'}\n"
    )
    
    # Resume / Progress Context
    resume_block = ""
    if start_at or progress_history:
        history_str = json.dumps(progress_history, indent=2) if progress_history else "{}"
        resume_block = (
            f"RESUME CONTEXT / PROGRESS:\n"
            f"The user is resuming a session or has already provided some answers.\n"
            f"- START_AT_NODE: {start_at}\n"
            f"- EXISTING_ANSWERS (Do not ask these again): {history_str}\n"
            f"INSTRUCTION: Start the conversation immediately at the node '{start_at}'. "
            f"Assume the values in EXISTING_ANSWERS are true and use them for ANY logic calculations immediately.\n"
        )

    grounding = (
        "STRICT SCRIPT ADHERENCE & LOGIC ENFORCEMENT:\n"
        "1. SOURCE OF TRUTH: The provided 'scriptData' (in declarative context) is the SUPREME LAW.\n"
        "2. FLOW CONTROL: You act as a state machine engine for this script.\n"
        "   - Read the current Step/Question ID.\n"
        "   - Wait for User Input.\n"
        "   - CALCULATION: If the script says 'If score > 2', you MUST mentally calculate the score from previous answers.\n"
        "   - BRANCHING: Execute the 'Next Step' logic strictly. Do NOT skip steps or jump ahead unless logic dictates.\n"
        "3. PROHIBITIONS: Do NOT add 'filler' conversation unless it helps build rapport specifically allowed by the script tone.\n"
        "4. RECOVERY: If the user provides an invalid answer (e.g., text for a slider), politely reprompt using the Script's clarification logic.\n"
    )

    a2ui = build_a2ui_instruction()

    safety = build_escalation_addendum(active.escalation_protocols)

    return "\n\n".join([header.strip(), script_meta.strip(), resume_block.strip(), grounding.strip(), a2ui.strip(), safety.strip()])


def build_live_grounding_bundle(
    *,
    active: ActiveScript,
    include_declarative_context: bool = True,
) -> Dict[str, Any]:
    """
    Convenience bundle for a Live session configuration layer.
    """
    bundle: Dict[str, Any] = {
        "system_instruction": build_system_instruction(active),
        "script_id": active.script_id,
        "version": active.version,
    }
    if include_declarative_context:
        bundle["declarative_context"] = build_declarative_context(active)
    return bundle


def build_turn_instruction_if_needed(active: ActiveScript, *, user_text: str) -> Optional[str]:
    """
    For per-turn updates: if high-risk is detected in the latest user input, return the
    safety override instructions to append to the model's context for that turn.
    """
    if contains_high_risk_symptom(user_text):
        # Do not log user_text. Only log that the gate triggered.
        logger.warning(
            "High-risk symptom detected; escalation override should be applied",
            event_type=EventType.SECURITY_SUSPICIOUS_ACTIVITY,
            script_id=active.script_id,
            version=active.version,
            gate="high_risk_symptom",
            triggered=True,
        )
        return build_escalation_addendum(active.escalation_protocols)
    return None


