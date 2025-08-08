"""Configuration file template for FastAPI app.

Remane config_sample.py to config.py if you use config.py
"""

from enum import StrEnum


#  SECTION:=============================================================
#            Secrets
#  =====================================================================


# Secret values
class Secrets(StrEnum):
    GAS_ID = "YOUR ID"
    API_KEY_GOOGLE = "YOUR KEY"


#  SECTION:=============================================================
#            Basic configs
#  =====================================================================


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


#  SECTION:=============================================================
#            Features, added
#  =====================================================================


class LoggingConfig(StrEnum):
    ENABLE = "True"
    FILEPATH = "/tmp/logfile_from_fastapi.log"
    TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
    FINAL_TEXT_ENABLE = "True"
    TRANSLATION_ENABLE = "True"


# Transaltor settings
class Translation(StrEnum):
    # ENABLE = "False"
    ENABLE = "True"
    SOURCE_LANGUAGE = "ja"
    TARGET_LANGUAGE = "en"


class VoicevoxConfig(StrEnum):
    ENABLE = "True"


#  SECTION:=============================================================
#            Constants, others
#  =====================================================================

# loop interval(second) of websocket for obs-speech-overlay
WAITING_LOOP_SEC = 1


# TODO: need to change
from enum import Enum

VOICEVOX_HOST = "127.0.0.1"
VOICEVOX_PORT = 50021


class VOICEVOX_MALE(Enum):
    SPEAKER = 13
    SPEED = 1.2
    PITCH = 1.0
    INTONATION = 1.0
    VOLUME = 1.0


class VOICEVOX_FEMALE(Enum):
    SPEAKER = 14
    SPEED = 1.2
    PITCH = 1.0
    INTONATION = 1.0
    VOLUME = 1.0
