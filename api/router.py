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
import logging

from api.ws_handler import WsMessageProcessor
from config import Endpoints, Htmls, WAITING_LOOP_SEC

#  SECTION:=============================================================
#            Logger
#  =====================================================================

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# SECTION:=============================================================
#           Attributes
# =====================================================================

# Main module imports this router
router = APIRouter()

# set template directory
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# Store websocket to send message to obs-speech-overlay.html
ws_obs_speech_overlay: WebSocket | None = None


# SECTION:=============================================================
#           Functions
# =====================================================================


def task_done_callback(task: asyncio.Task):
    """Handle task completion, log exceptions if any."""
    try:
        task.result()  # This will raise exception if task failed
    except Exception as e:
        logger.error(f"Task raised exception: {e}")


def schedule_task(task: asyncio.Task, tasks_set: set):
    """
    Schedule a given asyncio.Task by adding to the global tasks set
    and attaching callbacks for exception handling and cleanup.
    """
    task.add_done_callback(task_done_callback)
    tasks_set.add(task)
    task.add_done_callback(tasks_set.discard)


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
            logger.error(
                "websocket: obs-speech-overlay does not connect within timeout"
            )
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
    logger.info("Waiting for websocket:speech-recognition.")
    logger.info(
        f"websocket:obs-speech-overlay exists now? : {ws_obs_speech_overlay is not None}"
    )
    await websocket.accept()
    # Wati for target websocket to connect. target is ws_obs_speech_overlay, not this websocket.
    await wait_external_websocket_connects(ws_obs_speech_overlay)

    # Create an instance of MessagePrpocessor so translator persists per connection
    processor = WsMessageProcessor()

    # A per-connection set of running tasks
    running_tasks = set()

    try:
        while True:
            message = await websocket.receive_text()
            if ws_obs_speech_overlay is None:
                logger.error("websocket: obs-speech-overlay does not connect")
                break
            task = asyncio.create_task(
                processor.process_ws_message(websocket, ws_obs_speech_overlay, message)
            )
            schedule_task(task, running_tasks)
    except WebSocketDisconnect:
        logger.error("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cancel any remaining tasks when connection closes
        if running_tasks:
            logger.info(
                f"Cancelling {len(running_tasks)} running tasks for disconnected client."
            )
            for task in running_tasks:
                task.cancel()
            await asyncio.gather(*running_tasks, return_exceptions=True)
            running_tasks.clear()  # Optional: Cancel remaining tasks related to this connection


# WebSocket endpoint where obs-speech-overlay script connects
# For sending message to OBS. Nothing to be received.
# Keep websocket connection with while loop
@router.websocket(Endpoints.OBS_SPEECH_OVERLAY_WS)
async def websocket_obs_speech_overlay(websocket: WebSocket):
    global ws_obs_speech_overlay
    logger.info("Waiting for websocket:obs-speech-overlay.")
    # When OBS browser source starts, websocket between fast api and OBS establishes.
    await websocket.accept()
    # websocket has established, then store the websocket
    ws_obs_speech_overlay = websocket

    try:
        while True:
            # does not expect receiving data.
            await asyncio.sleep(WAITING_LOOP_SEC)
    except WebSocketDisconnect:
        logger.error("WebSocket disconnected")
        ws_obs_speech_overlay = None
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
