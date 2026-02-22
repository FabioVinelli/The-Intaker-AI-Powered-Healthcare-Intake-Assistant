import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from google import genai
from google import genai
from google.genai import types

import sys
from pathlib import Path
# Add project root to path to allow imports from sibling services
try:
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
except Exception:
    pass

from services.scoring_engine.scorer import calculate_severity
from services.scoring_engine.loc_rules import determine_loc
from services.treatment_planner.generator import create_plan_from_scores

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-bridge")

# Initialize Firebase
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': os.getenv("FIREBASE_PROJECT_ID")
    })

app = FastAPI(title="The Intaker Voice Bridge")

# CORS (Adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global constants - gemini-2.0-flash-exp is stable for Live API
GEMINI_MODEL = "gemini-2.0-flash-exp"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not set. Voice bridge will fail to connect to Gemini.")
    client = None
else:
    # Initialize GenAI Client
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY, http_options={"api_version": "v1alpha"})
    except Exception as e:
        logger.error(f"Failed to initialize GenAI Client: {e}")
        client = None

async def verify_token(token: str = Query(...)) -> Dict[str, Any]:
    """
    Verifies Firebase ID token from query parameter.
    Returns user payload if valid, raises HTTPException otherwise.
    """
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

@app.get("/")
async def root():
    return {
        "service": "The Intaker Voice Bridge",
        "status": "online",
        "endpoints": {
            "health": "GET /health",
            "voice_stream": "WebSocket /ws/intake?token=<token>"
        },
        "mode": "LIVE" if not os.getenv("MOCK_GEMINI_LIVE") == "true" else "MOCK"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "voice-bridge"}

@app.websocket("/ws/intake")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    Main WebSocket endpoint for voice streaming.
    - Handshake: Verify token.
    - Loop: Bidirectional stream Audio/JSON between Client and Gemini.
    """
    user = None
    # 1. Verify Token
    if os.getenv("DISABLE_AUTH_FOR_TESTING") == "true":
        logger.info("Auth bypassed for testing")
        user = {"uid": "test-user"}
    else:
        try:
            # Manual verification
            user = firebase_auth.verify_id_token(token)
            logger.info(f"Connection authenticated for user: {user.get('uid')}")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return

    await websocket.accept()

    if not client:
        logger.error("Gemini client not initialized")
        await websocket.close(code=1011, reason="Server configuration error: Gemini client unavailable")
        return

    # Create config for Gemini Live API
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction="""You are a compassionate clinical intake specialist for The Intaker, 
        a substance abuse treatment intake system. You conduct warm, empathetic ASAM-based clinical 
        assessments. Keep your responses brief, calming, and professional. Ask one question at a time 
        and listen carefully to the patient's responses.""",
    )

    transcript_buffer = []

    async def finalize_intake():
        """
        Runs the Intake Logic: Score -> Plan -> Emit
        """
        full_transcript = " ".join(transcript_buffer)
        logger.info(f"Finalizing intake. Transcript length: {len(full_transcript)}")
        
        try:
            # 1. Score
            scores = calculate_severity(full_transcript)
            
            # 2. Level of Care
            loc = determine_loc(scores)
            
            # 3. Plan
            # Convert Enum keys to string for JSON serialization
            scores_serializable = {str(k): v for k, v in scores.items()}
            plan = create_plan_from_scores(scores, loc)
            
            # 4. Emit
            result_payload = {
                "type": "intake_result",
                "data": {
                    "asam_scores": scores_serializable,
                    "suggested_plan": plan,
                    "level_of_care": loc
                }
            }
            await websocket.send_json(result_payload)
            logger.info("Intake result sent.")
            
        except Exception as e:
            logger.error(f"Error during intake finalization: {e}")
            await websocket.send_json({"type": "error", "message": str(e)})

    # Mock Session Logic
    class MockResponse:
        def __init__(self, text=None, data=None):
            self.text = text
            self.data = data

    class MockLiveSession:
        def __init__(self):
            self.queue = asyncio.Queue()
        
        async def send(self, input, end_of_turn=False):
            if isinstance(input, str):
                # Echo text back to simulate model response for buffer
                await self.queue.put(MockResponse(text=f"Echo: {input}"))
            elif isinstance(input, dict) and "data" in input:
                # Audio input with MIME type - ignore in mock mode
                pass
            
        async def receive(self):
            while True:
                item = await self.queue.get()
                yield item
                
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc, tb):
            pass

    # Determine if we should use Mock Mode
    force_mock = os.getenv("MOCK_GEMINI_LIVE") == "true"
    use_mock = force_mock or (client is None)
    
    if use_mock:
        if force_mock:
            logger.warning("Using MOCK_GEMINI_LIVE (Forced by env var)")
        else:
            logger.warning("Using MOCK_GEMINI_LIVE (Fallback due to missing/invalid Client)")
        session_ctx = MockLiveSession()
    else:
        try:
            session_ctx = client.aio.live.connect(model=GEMINI_MODEL, config=config)
        except Exception as e:
            logger.error(f"Failed to connect to Gemini Live: {e}")
            logger.warning("Falling back to MOCK_GEMINI_LIVE")
            session_ctx = MockLiveSession()

    try:
        async with session_ctx as session:
            logger.info("Connected to session")
            
            # Send initial state
            await websocket.send_json({"type": "state", "payload": "listening"})

            # Trigger initial greeting from Gemini
            await session.send(input="Hello, I am ready for the intake.", end_of_turn=True)
            logger.info("Sent greeting prompt to Gemini")

            async def receive_from_client():
                """Reads from WebSocket and sends to Gemini."""
                logger.info("Starting client receiver task")
                try:
                    while True:
                        try:
                            # Wait for message with a timeout to allow checking for cancellation
                            message = await asyncio.wait_for(websocket.receive(), timeout=1.0)
                        except asyncio.TimeoutError:
                            continue
                        
                        if "bytes" in message:
                            data = message["bytes"]
                            # Send audio with proper MIME type wrapping per Gemini Live API
                            await session.send(input={"data": data, "mime_type": "audio/pcm"}, end_of_turn=False)
                        
                        elif "text" in message:
                            text_data = message["text"]
                            try:
                                msg_json = json.loads(text_data)
                                if msg_json.get("type") == "interrupt":
                                    pass
                                elif msg_json.get("type") == "finalize":
                                    logger.info("Received finalize command")
                                    await finalize_intake()
                                    return
                            except:
                                if text_data:
                                    logger.info(f"Sending text to Gemini: {text_data}")
                                    await session.send(input=text_data, end_of_turn=True)
                except WebSocketDisconnect:
                    logger.info("Client disconnected normally")
                except Exception as e:
                    logger.error(f"Error receiving from client: {e}")
                finally:
                    logger.info("Client receiver task ended")

            async def receive_from_gemini():
                """Reads from Gemini and sends to Client."""
                logger.info("Starting Gemini receiver task")
                try:
                    # Continuously receive from Gemini Live session
                    async for response in session.receive():
                        # Handle audio data - check for inline_data in parts
                        if response.server_content and response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    # Send audio bytes to client
                                    await websocket.send_bytes(part.inline_data.data)
                                if part.text:
                                    logger.info(f"Received Text: {part.text[:50]}...")
                                    transcript_buffer.append(part.text)
                        
                        # Also handle direct data/text attributes
                        if response.data:
                            await websocket.send_bytes(response.data)
                        
                        if response.text:
                            logger.info(f"Received Text from Gemini: {response.text[:50]}...")
                            transcript_buffer.append(response.text)
                            
                except Exception as e:
                    logger.error(f"Error receiving from Gemini: {e}")
                finally:
                    logger.info("Gemini receiver task ended")

            # Run both tasks
            consumer_task = asyncio.create_task(receive_from_client())
            producer_task = asyncio.create_task(receive_from_gemini())

            # Wait for EITHER the client to disconnect OR Gemini to fail/finish
            # If Gemini finishes (e.g. error), we probably want to keep client open or close with error?
            # For robustness, we usually want to keep client open unless client creates the disconnect.
            # But if Gemini dies, we can't do much.
            
            done, pending = await asyncio.wait(
                [consumer_task, producer_task],
                return_when=asyncio.ALL_COMPLETED,
            )

            logger.info(f"One task completed: {[t.get_name() for t in done]}")

            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    except Exception as e:
        logger.error(f"Session setup error: {e}")
        try:
            await websocket.close(code=1011, reason=f"Upstream error: {str(e)}")
        except:
            pass
    finally:
        logger.info("Session closed")
