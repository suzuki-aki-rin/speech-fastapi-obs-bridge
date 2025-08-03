import json

from fastapi import WebSocket
from api.translator import Translator


def build_message_to_OBS(text: str, is_final: bool, language_code: str) -> str:
    message = {
        "recogText": text,
        "isFinal": is_final,
        "languageCode": language_code,
        "type": "original",
    }
    return json.dumps(message, ensure_ascii=False)


async def process_ws_message(
    ws_speech_recog: WebSocket, ws_OBS_speech: WebSocket | None, message: str
):
    """
    Process the received JSON string from the WebSocket.
    Prints whether it's an interim or final result and the recognized text itself.
    """
    try:
        payload = json.loads(message)
        text = payload.get("recogText", "")
        is_final = payload.get("isFinal", False)
        language = payload.get("language", {})
        language_code = language.get("code")
        language_label = language.get("label")

        # console output
        if is_final:
            print(f"[Final  ] {language_code}:{text}")

        else:
            print(f"[Interim] {language_code}:{text}")

        if ws_OBS_speech:
            message_for_OBS = build_message_to_OBS(text, is_final, language_code)
            await ws_OBS_speech.send_text(message_for_OBS)

    except json.JSONDecodeError:
        print(f"Received non-JSON message: {message}")
    except Exception as e:
        print(f"Error processing WebSocket message: {e}")
