"""FastAPI router for handling WebSocket requests.

This module defines the API endpoints for handling WebSocket requests and
providing HTML responses for the OBS browser source and speech recognition.

Usage example:

  from fastapi import FastAPI
  from api.router import router

  app = FastAPI()
  app.include_router(router)
"""

from pathlib import Path

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio

from api.ws_handler import WsMessageProcessor
from config import Endpoints, Htmls, WAITING_LOOP_SEC


# SECTION:=============================================================
#           Attributes
# =====================================================================

# Main module imports this router
router = APIRouter()

# set template directory
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# Store websocket to send message to OBS-speech-overlay.html
ws_OBS_speech_overlay: WebSocket | None = None


# SECTION:=============================================================
#           Functions
# =====================================================================


async def wait_external_websocket_connects(external_socket):
    """Waits for the external WebSocket to connect.

    Args:
        external_socket (WebSocket): The external WebSocket to wait for.
    Returns:
        bool: True if the external WebSocket is connected, False otherwise.
    """
    # polling timeout 10sec
    timeout = 10
    # polling interval 0.5sec
    interval = 0.5
    elasped_time = 0
    while external_socket is None:
        if elasped_time > timeout:
            print("websocket: OBS-speech-overlay does not connect within timeout")
            return False

        # async wait
        await asyncio.sleep(interval)
        elasped_time = interval
    return True


# SECTION:=============================================================
#           Endpoints
# =====================================================================


# For Chrome browser to do speech recognition
@router.get(Endpoints.SPEECH_RECOGNITION, response_class=HTMLResponse)
async def speech_recognition(request: Request):
    return templates.TemplateResponse(
        f"{Htmls.SPEECH_RECOGNITION}", {"request": request}
    )


# For OBS browser source to show data
@router.get(Endpoints.OBS_SPEECH_OVERLAY, response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        f"{Htmls.OBS_SPEECH_OVERLAY}", {"request": request}
    )


# WebSocket endpoint where speech-recogniton script connects
# When receiving data from speech-recogniton script,
# process_ws_message starts.
@router.websocket(Endpoints.SPEECH_RECOGNITION_WS)
async def websocket_speech_recognition(websocket: WebSocket):
    await websocket.accept()

    # Create an instance of MessageProcessor so translator persists per connection
    processor = WsMessageProcessor()
    try:
        while True:
            message = await websocket.receive_text()
            await wait_external_websocket_connects(ws_OBS_speech_overlay)
            if ws_OBS_speech_overlay is None:
                print("websocket: OBS-speech-overlay does not connect")
                break
            asyncio.create_task(
                processor.process_ws_message(websocket, ws_OBS_speech_overlay, message)
            )
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")


# WebSocket endpoint where OBS-speech-overlay script connects
# For sending message to OBS. Nothing to be received.
# Keep websocket connection with while loop
@router.websocket(Endpoints.OBS_SPEECH_OVERLAY_WS)
async def websocket_obs_speech_overlay(websocket: WebSocket):
    global ws_OBS_speech_overlay
    # When OBS browser source starts, websocket between fast api and OBS establishes.
    await websocket.accept()
    # websocket has established, then store the websocket
    ws_OBS_speech_overlay = websocket
    # print(ws_OBS_speech_overlay)

    try:
        while True:
            # does not expect receiving data.
            await asyncio.sleep(WAITING_LOOP_SEC)
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        ws_OBS_speech_overlay = None
    except Exception as e:
        print(f"WebSocket error: {e}")
