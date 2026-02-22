import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

import functions_framework
from google.cloud import firestore


# -----------------------------------------------------------------------------
# HIPAA-safe structured logging (avoid logging request/response bodies)
# -----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _log(level: str, message: str, **fields: Any) -> None:
    payload = {
        "service": "intake_scripts_service",
        "message": message,
        **fields,
    }
    line = json.dumps(payload, default=str)
    getattr(logger, level.lower(), logger.info)(line)


# -----------------------------------------------------------------------------
# Firestore client (reuse across invocations)
# -----------------------------------------------------------------------------

try:
    DB = firestore.Client()
except Exception as e:
    _log("warning", "Failed to initialize Firestore client", error=str(e))
    DB = None


DEFAULT_SCRIPT_ID = os.getenv("DEFAULT_SCRIPT_ID", "full_asam_script_humanized")


def _cors_headers() -> Dict[str, str]:
    allow_origin = os.getenv("CORS_ALLOW_ORIGIN", "*")
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Max-Age": "3600",
    }


def _json_response(payload: Dict[str, Any], status: int) -> Tuple[str, int, Dict[str, str]]:
    headers = {"Content-Type": "application/json", **_cors_headers()}
    return json.dumps(payload), status, headers


def _pick_version(script_doc: Dict[str, Any], script_ref: firestore.DocumentReference) -> Optional[str]:
    """
    Determine active version using:
    - intake_scripts/{script_id}.latestVersion (preferred)
    - intake_scripts/{script_id}.version
    - else newest version doc where published == true (no orderBy to avoid composite indexes)
    """
    v = script_doc.get("latestVersion") or script_doc.get("version")
    if isinstance(v, str) and v.strip():
        return v.strip()

    # Fallback: find any published version documents and pick the most recently updated in code.
    try:
        published_snaps = list(script_ref.collection("versions").where("published", "==", True).stream())
    except Exception:
        return None

    def score(snap: firestore.DocumentSnapshot) -> str:
        d = snap.to_dict() or {}
        # Prefer updatedAt, then _updated_at, then createdAt, then document id
        return str(d.get("updatedAt") or d.get("_updated_at") or d.get("createdAt") or snap.id)

    if not published_snaps:
        return None

    best = max(published_snaps, key=score)
    return best.id


def _strip_firestore_metadata(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove common metadata fields so the frontend receives a clean script payload.
    """
    cleaned = dict(d)
    for k in [
        "_created_at",
        "_updated_at",
        "_version",
        "createdAt",
        "updatedAt",
        "source",
    ]:
        cleaned.pop(k, None)
    return cleaned


@functions_framework.http
def get_active_script(request):
    """
    HTTP Cloud Function: GetActiveScript

    Query param / JSON body:
      - script_id (optional, defaults to DEFAULT_SCRIPT_ID)

    Behavior:
      - Reads intake_scripts/{script_id}
      - Chooses version via latestVersion/version pointer, else published == true version doc
      - Fetches versions/{version}.scriptData
      - Returns a clean JSON object containing intake logic (and components if present)
    """
    # CORS preflight
    if request.method == "OPTIONS":
        return ("", 204, _cors_headers())

    if DB is None:
        _log("error", "Firestore client not initialized")
        return _json_response(
            {"ok": False, "error": {"code": "firestore_unavailable", "message": "Firestore client not initialized"}},
            500,
        )

    # Accept either query string or JSON body
    request_json = request.get_json(silent=True) or {}
    script_id = (request.args.get("script_id") if hasattr(request, "args") else None) or request_json.get("script_id")
    script_id = (script_id or DEFAULT_SCRIPT_ID).strip()

    if not script_id:
        return _json_response(
            {"ok": False, "error": {"code": "invalid_request", "message": "script_id must be provided"}},
            400,
        )

    try:
        script_ref = DB.collection("intake_scripts").document(script_id)
        script_snap = script_ref.get()

        if not script_snap.exists:
            _log("info", "Script not found", script_id=script_id)
            return _json_response(
                {"ok": False, "error": {"code": "not_found", "message": "Script not found"}, "script_id": script_id},
                404,
            )

        script_doc = script_snap.to_dict() or {}
        version = _pick_version(script_doc, script_ref)
        if not version:
            _log("warning", "No active version found for script", script_id=script_id)
            return _json_response(
                {
                    "ok": False,
                    "error": {"code": "no_active_version", "message": "No active version found for script"},
                    "script_id": script_id,
                },
                404,
            )

        version_ref = script_ref.collection("versions").document(version)
        version_snap = version_ref.get()
        if not version_snap.exists:
            _log("warning", "Version document missing", script_id=script_id, version=version)
            return _json_response(
                {
                    "ok": False,
                    "error": {"code": "version_not_found", "message": "Version not found"},
                    "script_id": script_id,
                    "version": version,
                },
                404,
            )

        version_doc_raw = version_snap.to_dict() or {}
        version_doc = _strip_firestore_metadata(version_doc_raw)

        script_data = version_doc.get("scriptData")
        if not isinstance(script_data, dict):
            _log("error", "Version missing scriptData", script_id=script_id, version=version)
            return _json_response(
                {
                    "ok": False,
                    "error": {"code": "invalid_script", "message": "Version document missing scriptData"},
                    "script_id": script_id,
                    "version": version,
                },
                500,
            )

        # Optional: include components (stored as root-level docs under components/)
        components: Dict[str, Any] = {}
        try:
            scoring_snap = version_ref.collection("components").document("scoring_weights").get()
            if scoring_snap.exists:
                d = scoring_snap.to_dict() or {}
                if isinstance(d.get("scoring_weights"), dict):
                    components["scoring_weights"] = d["scoring_weights"]
        except Exception as e:
            _log("warning", "Failed to read scoring_weights component", script_id=script_id, version=version, error=str(e))

        try:
            escalation_snap = version_ref.collection("components").document("escalation_protocols").get()
            if escalation_snap.exists:
                d = escalation_snap.to_dict() or {}
                if isinstance(d.get("escalation_protocols"), dict):
                    components["escalation_protocols"] = d["escalation_protocols"]
        except Exception as e:
            _log(
                "warning",
                "Failed to read escalation_protocols component",
                script_id=script_id,
                version=version,
                error=str(e),
            )

        response = {
            "ok": True,
            "script_id": script_id,
            "version": version,
            "script_name": version_doc.get("script_name") or script_doc.get("name"),
            "description": version_doc.get("description") or script_doc.get("description"),
            "published": bool(version_doc.get("published") or script_doc.get("published")),
            "scriptData": script_data,
        }
        if components:
            response["components"] = components

        _log("info", "Active script fetched", script_id=script_id, version=version)
        return _json_response(response, 200)

    except Exception as e:
        _log("error", "Unhandled error in get_active_script", script_id=script_id, error=str(e))
        return _json_response(
            {"ok": False, "error": {"code": "internal", "message": "Internal server error"}},
            500,
        )


