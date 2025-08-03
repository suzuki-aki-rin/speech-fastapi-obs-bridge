from enum import StrEnum


# Remane config_sample.py to config.py if you use config.py


# Secret values
class Secrets(StrEnum):
    GAS_ID = "YOUR ID"
    API_KEY_GOOGLE = "YOUR KEY"


class Endpoints(StrEnum):
    SPEECH_RECOGNITION = "/speech-recognition"
    SPEECH_RECOGNITION_WS = "/ws/speech-recognition"
    OBS_SPEECH_OVERLAY = "/obs-speech-overlay"
    OBS_SPEECH_OVERLAY_WS = "/ws/obs-speech-overlay"


# StrEnum Object acts like str but it is not str.
# So, pass EnumStr to Jinja2Templates, then error happens.
class Htmls(StrEnum):
    SPEECH_RECOGNITION = "speech-recognition.html"
    OBS_SPEECH_OVERLAY = "obs-speech-overlay.html"


class Urls(StrEnum):
    GAS_BASE_URL = "https://script.google.com/macros/s/" + Secrets.GAS_ID + "/exec"


# loop interval(second) of websocket for obs-speech-overlay
WAITING_LOOP_SEC = 1
