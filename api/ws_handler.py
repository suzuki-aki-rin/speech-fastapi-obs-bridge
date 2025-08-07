import json
import logging

from fastapi import WebSocket

from api.translator import Translator
from config import Translation


#  SECTION:=============================================================
#            Logger
#  =====================================================================

# Setup main logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


#  SECTION:=============================================================
#            Functions, utility
#  =====================================================================k


def build_message_to_obs(text: str, is_final: bool, language_code: str) -> str:
    message = {
        "recogText": text,
        "isFinal": is_final,
        "languageCode": language_code,
        "type": "original",
    }
    return json.dumps(message, ensure_ascii=False)


def shorten_language_code(language_code: str) -> str:
    return language_code[:2]


#  SECTION:=============================================================
#            Class
#  =====================================================================


class WsMessageProcessor:
    translator: Translator | None

    def __init__(self):
        self.translator = None

    def _loginfo_recognition_text(
        self, recognition_text: str, is_final: bool, language_code: str
    ) -> None:
        is_final_text = "[Final  ]" if is_final else "[Interim]"
        logger.info(f"{is_final_text} {language_code}: {recognition_text}")

    #  SECTION:=============================================================
    #            Functions, helper
    #  =====================================================================

    def _unpack_message(
        self, message: str
    ) -> tuple[str, bool, str | None, str | None] | None:
        """
        Parse the incoming JSON message and extract relevant info.

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

        # Log recognition text
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
            if Translation.ENABLE == "True":
                # Translate text
                result = await self._translate_text(recog_text, language_code or "")
                result_json = json.dumps(result, ensure_ascii=False)
                # Send translated text to OBS
                await self._send_to_obs(ws_message_target, result_json)
