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


def print_message(message: str, is_final: bool, language_code: str) -> None:
    is_final_text = "[Final  ]" if is_final else "[Interim]"
    logger.info(f"{is_final_text} {language_code}: {message}")


def shorten_language_code(language_code: str) -> str:
    return language_code[:2]


#  SECTION:=============================================================
#            Class
#  =====================================================================


class WsMessageProcessor:
    translator: Translator | None

    def __init__(self):
        self.translator = None

    async def process_ws_message(
        self,
        ws_message_source: WebSocket,
        ws_message_target: WebSocket | None,
        message: str,
    ) -> None:
        """Main entry point to process a WebSocket message."""
        try:
            # JSON decode
            payload = json.loads(message)
            text: str = payload.get("recogText", "")
            is_final: bool = payload.get("isFinal", False)
            language: dict | None = payload.get("language", {})
            language_code: str | None = language.get("code") if language else None
            language_label: str | None = language.get("label") if language else None

            # send to OBS
            if ws_message_target:
                message_for_obs = build_message_to_obs(
                    text, is_final, language_code or ""
                )
                await ws_message_target.send_text(message_for_obs)

            # console output
            print_message(text, is_final, language_code or "")

            # Do if recognition text is final
            if is_final:
                # send to Translator
                if Translation.ENABLE == "True":
                    if Translation.SOURCE_LANGUAGE != shorten_language_code(
                        language_code or ""
                    ):
                        raise ValueError(
                            f"language code mismatch: {Translation.SOURCE_LANGUAGE} != {language_code}"
                        )
                    else:
                        # translator is created once
                        if self.translator is None:
                            self.translator = Translator(
                                Translation.SOURCE_LANGUAGE, Translation.TARGET_LANGUAGE
                            )
                        json_result = await self.translator.translate_as_json(text)
                        if ws_message_target:
                            await ws_message_target.send_text(json_result)

        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message: {message}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
