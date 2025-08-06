import json

from fastapi import WebSocket
from api.translator import Translator
from config import Translation


def build_message_to_obs(text: str, is_final: bool, language_code: str) -> str:
    message = {
        "recogText": text,
        "isFinal": is_final,
        "languageCode": language_code,
        "type": "original",
    }
    return json.dumps(message, ensure_ascii=False)


def print_message(message: str, is_final: bool, language_code: str):
    is_final_text = "[Final  ]" if is_final else "[Interim]"

    print(f"{is_final_text} {language_code}:{message}")


def shorten_language_code(language_code: str) -> str:
    return language_code[:2]


class WsMessageProcessor:
    def __init__(self):
        self.translator = None

    async def process_ws_message(
        self,
        ws_message_source: WebSocket,
        ws_messgae_target: WebSocket | None,
        message: str,
    ):
        """
        Process the received JSON string from the WebSocket.
        Prints whether it's an interim or final result and the recognized text itself.
        """
        try:
            # JSON decode
            payload = json.loads(message)
            text = payload.get("recogText", "")
            is_final = payload.get("isFinal", False)
            language = payload.get("language", {})
            language_code = language.get("code")
            language_label = language.get("label")

            # send to OBS
            if ws_messgae_target:
                message_for_obs = build_message_to_obs(text, is_final, language_code)
                await ws_messgae_target.send_text(message_for_obs)

            # console output
            print_message(text, is_final, language_code)

            if is_final:
                # send to Translator
                if Translation.ENABLE == "True":
                    if Translation.SOURCE_LANGUAGE != shorten_language_code(
                        language_code
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
                        json_result = self.translator.translate(text)
                        if ws_messgae_target:
                            await ws_messgae_target.send_text(json_result)

        except json.JSONDecodeError:
            print(f"Received non-JSON message: {message}")
        except Exception as e:
            print(f"Error processing WebSocket message: {e}")
