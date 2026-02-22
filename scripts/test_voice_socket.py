import asyncio
import websockets
import json
import os
import sys

# Configuration
# Allow overriding URI via env var
URI = os.getenv("WS_URI", "ws://localhost:8080/ws/intake?token=test-token")

async def test_connection():
    print(f"Connecting to {URI}...")
    try:
        async with websockets.connect(URI) as websocket:
            print("✅ Connected!")
            
            # Expect "state": "listening"
            try:
                initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Incoming: {initial_msg}")
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for initial state.")
            
            # Send dummy audio (silence or noise)
            # 1 second of silence at 16kHz, 16-bit mono = 32000 bytes
            # We send a smaller chunk
            dummy_audio = bytes([0] * 3200) 
            
            print("Sending dummy audio chunk...")
            await websocket.send(dummy_audio)
            
            # Wait for response (timeout 5s)
            print("Waiting for response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                if isinstance(response, bytes):
                    print(f"✅ Received audio bytes: {len(response)} bytes")
                else:
                    print(f"✅ Received text: {response}")
            except asyncio.TimeoutError:
                print("⚠️ No response from Gemini (expected if dummy audio is silence)")
            
            print("Closing connection...")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection())
