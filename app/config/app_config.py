from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import tomllib


#  SECTION:=============================================================
#            Constants
#  =====================================================================

TOML_PATH = "app/config/app_config.toml"

#  SECTION:=============================================================
#            Basic configs
#  =====================================================================


class EndpointConfig(BaseModel):
    speech_recognition: str
    speech_recognition_ws: str
    obs_speech_overlay: str
    obs_speech_overlay_ws: str


class HtmlConfig(BaseModel):
    speech_recognition: str
    obs_speech_overlay: str


class HeartbeatConfig(BaseModel):
    text: str
    interval: int
    timeout: int


#  SECTION:=============================================================
#            Additinal features
#  =====================================================================


class LoggingConfig(BaseModel):
    enable: bool
    filepath: str
    timestamp_format: str
    final_text_enable: bool
    translation_enable: bool


class TranslationConfig(BaseModel):
    enable: bool
    source_language: str
    target_language: str
    api_type: str
    api_base_url: str
    api_url: str


class VoicevoxMaleVoiceConfig(BaseModel):
    speaker: int
    speed: float
    pitch: float
    intonation: float
    volume: float


class VoicevoxFemaleVoiceConfig(BaseModel):
    speaker: int
    speed: float
    pitch: float
    intonation: float
    volume: float


class VoicevoxServerConfig(BaseModel):
    host: str
    port: int


class VoicevoxConfig(BaseModel):
    enable: bool
    server: VoicevoxServerConfig
    male_voice: VoicevoxMaleVoiceConfig
    female_voice: VoicevoxFemaleVoiceConfig


class AppConfig(BaseSettings):
    # secret values
    gas_id: str

    endpoints: EndpointConfig
    htmls: HtmlConfig
    heartbeat: HeartbeatConfig
    logging: LoggingConfig
    translation: TranslationConfig
    voicevox: VoicevoxConfig

    model_config = SettingsConfigDict(secrets_dir="secrets")

    # ---- Runs automatically after parsing TOML ----
    @model_validator(mode="after")
    def substitute_placeholders(self):
        if self.translation.api_type == "gas":
            """Replace placeholders like {gas_id} in URLs using values from 'secret'."""
            # Example: replace {gas_id} in gas_base_url
            self.translation.api_url = self.translation.api_base_url.format(
                gas_id=self.gas_id
            )
        return self


# --- Loader ---
def load_config(path: str | Path = TOML_PATH) -> AppConfig:
    with Path(path).open("rb") as f:
        toml_dict = tomllib.load(f)
    return AppConfig(**toml_dict)


# Global config instance
app_config = load_config()


def main():
    print(app_config.heartbeat.interval)
    print(app_config.voicevox.female_voice)
    print(app_config.translation.api_url)


if __name__ == "__main__":
    main()
