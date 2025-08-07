"""
Provides a class for handling WebSocket messages and translating text.

Examples:

  from api.ws_handler import WebSocketMessageProcessor

  processor = WebSocketMessageProcessor()
  await processor.process_ws_message(websocket, ws_OBS_speech_overlay, message)
"""

import json
import logging

from datetime import datetime
from enum import Enum

from fastapi import WebSocket

from api.translator import Translator
from config import LoggingConfig, Translation

#  SECTION:=============================================================
#            Constatnts
#  =====================================================================


class LogType(Enum):
    """LogType enum for _log_selected_to_file method."""

    FINAL = "final"
    TRANSLATION = "translation"
    # add other types and flags here as needed


#  SECTION:=============================================================
#            Logger
#  =====================================================================

# Setup main logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

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


#  SECTION:=============================================================
#            Class
#  =====================================================================


class WsMessageProcessor:
    """class for handling WebSocket messages and translating text."""

    translator: Translator | None
    LOG_FILE_PATH = LoggingConfig.FILEPATH
    LOG_FILE_TIMESTAMP_FORMAT = LoggingConfig.TIMESTAMP_FORMAT

    def __init__(self):
        self.translator = None

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
            LogType.FINAL: LoggingConfig.FINAL_TEXT_ENABLE,
            LogType.TRANSLATION: LoggingConfig.TRANSLATION_ENABLE,
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
        if Translation.SOURCE_LANGUAGE != shorten_language_code(
            text_language_code or ""
        ):
            raise ValueError(
                f"language code mismatch: {Translation.SOURCE_LANGUAGE} != {text_language_code}"
            )
        else:
            if self.translator is None:
                self.translator = Translator(
                    Translation.SOURCE_LANGUAGE, Translation.TARGET_LANGUAGE
                )
            result = await self.translator.translate_as_dict(text_to_translate)
            return result

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
            if LoggingConfig.ENABLE == "True":
                self._log_selected_to_file(recog_text, LogType.FINAL)

            # Translate final text
            if Translation.ENABLE == "True":
                # Translate text
                result = await self._translate_text(recog_text, language_code or "")
                # Log translated text file if needed.
                self._log_selected_to_file(
                    result["translated_text"], LogType.TRANSLATION
                )
                result_json = json.dumps(result, ensure_ascii=False)
                # Send translated text to OBS
                await self._send_to_obs(ws_message_target, result_json)
                # Log translated text to console and file if needed.
