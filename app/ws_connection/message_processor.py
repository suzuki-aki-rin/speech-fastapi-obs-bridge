"""
Provides a class for handling WebSocket messages and translating text.

Examples:

  from api.ws_handler import WebSocketMessageProcessor

  processor = WebSocketMessageProcessor()
  await processor.process_ws_message(websocket, ws_OBS_speech_overlay, message)
"""

import json
import logging
import asyncio

from datetime import datetime
from enum import Enum

from fastapi import WebSocket

from api.translator import Translator
from api.voicevox_engine_util import voicevox_say_female_async
from config.config import app_config

#  SECTION:=============================================================
#            Logger
#  =====================================================================

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# # Setup separate logger for final texts and/or translated texts
# # (disabled by default)
# # This logger does not log to file in FastAPI app.
#
# file_logger = logging.getLogger("file_logger")
# file_logger.setLevel(logging.INFO)
#
# # Prevent adding multiple handlers if this code is run multiple times
# if not file_logger.hasHandlers():
#     if LoggingConfig.ENABLE:
#         # file_handler = logging.FileHandler("final_texts.log", encoding="utf-8")
#         file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
#         file_handler.setLevel(logging.INFO)
#         formatter = logging.Formatter("%(asctime)s - %(message)s")
#         file_handler.setFormatter(formatter)
#         file_logger.addHandler(file_handler)
#     else:
#         # If logging disabled, add NullHandler to avoid "No handler found" warnings
#         file_logger.addHandler(logging.NullHandler())

#  SECTION:=============================================================
#            Constatnts
#  =====================================================================


class LogType(Enum):
    """LogType enum for _log_selected_to_file method."""

    FINAL = "final"
    TRANSLATION = "translation"
    # add other types and flags here as needed


#  SECTION:=============================================================
#            Functions, utility
#  =====================================================================


def build_message_to_obs(text: str, is_final: bool, language_code: str) -> str:
    """Build and return a message to be sent to OBS.

    Args:
        text (str): The text to be displayed in OBS.
        is_final (bool): Whether the message is final or not.
        language_code (str): The language code of the message.

    Returns:
        str: The JSON message to be sent to OBS.
    """
    message = {
        "recogText": text,
        "isFinal": is_final,
        "languageCode": language_code,
        "type": "original",
    }
    return json.dumps(message, ensure_ascii=False)


def shorten_language_code(language_code: str) -> str:
    """Shorten language code to 2 letters."""
    return language_code[:2]


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


#  SECTION:=============================================================
#            Class
#  =====================================================================


class WsMessageProcessor:
    """class for handling WebSocket messages and translating text."""

    translator: Translator | None
    LOG_FILE_PATH = app_config.logging.filepath
    LOG_FILE_TIMESTAMP_FORMAT = app_config.logging.timestamp_format

    def __init__(self):
        self.translator = None
        self._send_lock = asyncio.Lock()
        self._running_tasks = set()

    #  SECTION:=============================================================
    #            Functions, helper
    #  =====================================================================

    def _log_selected_to_file(self, text: str, log_type: LogType) -> None:
        """
        Write text to the log file only if the corresponding flags are enabled.

        Flags are written in LoggingConfig.
        This implementation uses direct file I/O to avoid conflicts with FastAPI's logging.

        Note:
          Before using this method, check LogType class, LogginConfig and flag_map.
        """
        # Define a mapping from LogType to the corresponding flag
        flag_map = {
            LogType.FINAL: app_config.logging.final_text_enable,
            LogType.TRANSLATION: app_config.logging.translation_enable,
            # add other types and flags here as needed
        }

        if not flag_map.get(log_type, False):
            return  # Do not log if flag is False or log_type unknown

        log_time_stamp_format = self.LOG_FILE_TIMESTAMP_FORMAT or "%Y-%m-%d %H:%M:%S"

        timestamp = datetime.now().strftime(log_time_stamp_format)
        log_entry = f"{timestamp} - {text} - {log_type.value}\n"

        # Open the log file in append mode with UTF-8 encoding
        try:
            with open(self.LOG_FILE_PATH, mode="a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            # Optionally handle or print the error; here we just print to stderr
            print(f"Failed to write to log file {self.LOG_FILE_PATH}: {e}")

    def _loginfo_recognition_text(
        self, recognition_text: str, is_final: bool, language_code: str
    ) -> None:
        """Log the recognition text with appropriate prefix."""
        is_final_text = "[Final  ]" if is_final else "[Interim]"
        logger.info(f"{is_final_text} {language_code}: {recognition_text}")

    def _unpack_message(
        self, message: str
    ) -> tuple[str, bool, str | None, str | None] | None:
        """
        Parse the incoming JSON message and extract relevant info.

        Args:
            message (str): The JSON message to parse.

        Returns:
            tuple: (reocg_text, is_final, language_code, language_label)
        """
        try:
            payload = json.loads(message)
            recog_text: str = payload.get("recogText", "")
            is_final: bool = payload.get("isFinal", False)
            language: dict | None = payload.get("language", {})
            language_code: str | None = language.get("code") if language else None
            language_label: str | None = language.get("label") if language else None
            return recog_text, is_final, language_code, language_label
        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message: {message}")
            return None

    async def _send_to_obs(
        self, ws_target: WebSocket | None, message_json: str
    ) -> None:
        """Send the message json_encoded to the target WebSocket."""
        if not ws_target:
            logger.error("No target WebSocket available")
            return
        try:
            async with self._send_lock:
                await ws_target.send_text(message_json)
        except Exception as e:
            logger.error(f"Error sending message to OBS: {e}", exc_info=True)

    async def _translate_text(
        self, text_to_translate: str, text_language_code: str
    ) -> dict:
        """
        Translate the text using Translator and return dict result.

        Initializes Translator if not already initialized.
        The initialization uses Translation in config.py
        """
        # Check if source language of config.py matches the language of text to translate
        if app_config.translation.source_language != shorten_language_code(
            text_language_code or ""
        ):
            raise ValueError(
                f"language code mismatch: {app_config.translation.source_language} != {text_language_code}"
            )
        else:
            if self.translator is None:
                self.translator = Translator(
                    app_config.translation.source_language,
                    app_config.translation.target_language,
                )
            result = await self.translator.translate_as_dict(text_to_translate)
            return result

    async def translate_and_send_to_obs(
        self,
        ws_target: WebSocket | None,
        text_to_translate: str,
        text_language_code: str,
    ) -> None:
        try:
            translation_result = await self._translate_text(
                text_to_translate, text_language_code
            )
            # Log translated text to log file
            self._log_selected_to_file(
                translation_result["translated_text"], LogType.TRANSLATION
            )
            translation_json = json.dumps(translation_result)
            await self._send_to_obs(ws_target, translation_json)
        except Exception as e:
            logger.error(f"Error translating text: {e}", exc_info=True)

    #  SECTION:=============================================================
    #            Functions, main
    #  =====================================================================

    async def process_ws_message(
        self,
        ws_message_source: WebSocket,
        ws_message_target: WebSocket | None,
        message: str,
    ) -> None:
        """Main entry point to process a WebSocket message."""

        # Unpack received message
        unpacked = self._unpack_message(message)
        if unpacked is None:
            return
        recog_text, is_final, language_code, language_label = unpacked

        # Log recognition text to console and file if needed.
        self._loginfo_recognition_text(recog_text, is_final, language_code or "")

        # Send message to OBS, regardless of weather the recognition text is final or not
        # Build and send message for OBS
        message_for_obs = build_message_to_obs(
            recog_text, is_final, language_code or ""
        )
        await self._send_to_obs(ws_message_target, message_for_obs)

        #  SECTION:=============================================================
        #           Do if recognition text is final
        #  =====================================================================

        # Pass recognition text to other modules
        # Toggle the modules by config.py
        if is_final:
            # Log final text to console
            if app_config.logging.enable:
                self._log_selected_to_file(recog_text, LogType.FINAL)
            # Voicevox
            if app_config.voicevox.enable:
                task = asyncio.create_task(voicevox_say_female_async(recog_text))
                schedule_task(task, self._running_tasks)

            # Translate final text
            if app_config.translation.enable:
                task = asyncio.create_task(
                    self.translate_and_send_to_obs(
                        ws_message_target,
                        recog_text,
                        language_code or "",
                    )
                )
                schedule_task(task, self._running_tasks)

            await asyncio.gather(*self._running_tasks, return_exceptions=True)
