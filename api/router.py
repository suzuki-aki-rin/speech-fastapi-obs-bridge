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
from api.ws_connection_manager import WsConnectionManager
from config import app_config

#  SECTION:=============================================================
#            Logger
#  =====================================================================

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)

# SECTION:=============================================================
#           Attributes
# =====================================================================

# Main module imports this router
router = APIRouter()

# set template directory
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# # Store websocket to send message to obs-speech-overlay.html
# ws_obs_speech_overlay: WebSocket | None = None

# Manage WebSocket connections with connection_manager
connection_manager = WsConnectionManager()


# SECTION:=============================================================
#           Functions, websocket
# =====================================================================


# async def heartbeat_and_check(
#     ws: WebSocket,
#     heartbeat_text=HEARTBEAT_TEXT,
#     interval: int = HEARTBEAT_INTERVAL,
#     timeout: int = HEARTBEAT_TIMEOUT,
# ):
# """Send heartbeat and check if the response is sent within the timeout."""
# try:
#     while True:
#         await asyncio.sleep(interval)
#         await ws.send_text(heartbeat_text)
#         logger.debug("Sent a heartbeat")
#         try:
#             async with asyncio.timeout(timeout):
#                 await ws.receive_text()
#                 logger.debug(
#                     "Recieved something after the heartbeat within the timeout"
#                 )
#         except asyncio.TimeoutError:
#             logger.error("Pong timeout - connection may be dead")
#             break
# except asyncio.CancelledError:
#     logger.info("Heartbeat task was cancelled")
# except WebSocketDisconnect as e:
#     logger.error(f"WebSocket disconnected. Code:{e.code} Heartbeat failed.")
# except Exception as e:
#     logger.error(f"Heartbeat failed: {e}")


async def heartbeat(
    ws: WebSocket,
    heartbeat_text=app_config.heartbeat.text,
    interval: int = app_config.heartbeat.interval,
):
    """Send heartbeat"""
    try:
        while True:
            await asyncio.sleep(interval)
            await ws.send_text(heartbeat_text)
            logger.debug("Sent a heartbeat")
    except asyncio.CancelledError:
        logger.info("Heartbeat task was cancelled")
    except WebSocketDisconnect as e:
        logger.error(f"WebSocket disconnected. Code:{e.code} Heartbeat failed.")
    except Exception as e:
        logger.error(f"Heartbeat failed: {e}")


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


#  SECTION:=============================================================
#            Functions, asyncio task management
#  =====================================================================


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


# SECTION:=============================================================
#           Endpoints
# =====================================================================


# For Chrome browser to do speech recognition
@router.get(app_config.endpoints.speech_recognition, response_class=HTMLResponse)
async def speech_recognition(request: Request):
    return templates.TemplateResponse(
        f"{app_config.htmls.speech_recognition}", {"request": request}
    )


# For OBS browser source to show data
@router.get(app_config.endpoints.obs_speech_overlay, response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        f"{app_config.htmls.obs_speech_overlay}", {"request": request}
    )


# WebSocket endpoint where speech-recogniton script connects
# When receiving data from speech-recogniton script,
# process_ws_message starts.
@router.websocket(app_config.endpoints.speech_recognition_ws)
async def websocket_speech_recognition(websocket: WebSocket):
    logger.debug("Waiting for websocket:speech-recognition.")
    logger.debug(
        f"websocket:obs-speech-overlay is connected? : {connection_manager.is_connected('ws_obs_speech_overlay')}"
    )
    await websocket.accept()
    connection_manager.add("ws_speech_recognition", websocket=websocket)

    # # Wati for target websocket to connect. target is ws_obs_speech_overlay, not this websocket.
    # isconnected_obs = await wait_external_websocket_connects(ws_obs_speech_overlay)
    # if not isconnected_obs:
    #     logger.error("websocket: obs-speech-overlay does not connect")
    #     return
    #
    # logger.debug(
    #     f"websocket:obs-speech-overlay is connected? : {ws_obs_speech_overlay is not None}"
    # )

    # Create an instance of MessagePrpocessor so translator persists per connection
    processor = WsMessageProcessor()
    # A per-connection set of running tasks
    running_tasks = set()

    try:
        while True:
            message = await websocket.receive_text()
            logger.debug("/speech-recognition recieved message.")

            target_ws = connection_manager.get("ws_obs_speech_overlay")
            if target_ws is None:
                logger.error("websocket: obs-speech-overlay is not connected")
            else:
                task = asyncio.create_task(
                    processor.process_ws_message(websocket, target_ws, message)
                )
                schedule_task(task, running_tasks)
    except WebSocketDisconnect as e:
        logger.error(f"WebSocket: speech-recognition is disconnected. Code:{e.code}")
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
        # Remove WebSocket connection in this endpoint.
        connection_manager.remove("ws_speech_recognition")


# WebSocket endpoint where obs-speech-overlay script connects
# For sending message to OBS. Nothing to be received.
# Keep websocket connection with while loop
@router.websocket(app_config.endpoints.obs_speech_overlay_ws)
async def websocket_obs_speech_overlay(websocket: WebSocket):
    logger.debug("Waiting for websocket:obs-speech-overlay.")
    # When OBS browser source starts, websocket between fast api and OBS establishes.
    await websocket.accept()
    # websocket has established, then store the websocket
    connection_manager.add("ws_obs_speech_overlay", websocket=websocket)
    logger.debug("webSocket:obs-speech-overlay is set.")

    # Send heartbeat to websocket: obs-speech-overlay
    task_heartbeat = asyncio.create_task(heartbeat(websocket), name="heartbeat")
    try:
        while not task_heartbeat.done():
            # Receive text from websocket: obs-speech-overlay, only pong.
            await websocket.receive_text()  # discard or use
    except WebSocketDisconnect as e:
        logger.error(f"WebSocket:obs-speech-overlay is disconnected. Code: {e.code}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connection_manager.remove("ws_obs_speech_overlay")
        logger.debug("webSocket:obs-speech-overlay is removed")
