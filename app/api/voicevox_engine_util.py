import asyncio
import logging

import httpx
import requests

import io
import wave
import simpleaudio as sa


#  SECTION:=============================================================
#            Logger
#  =====================================================================

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

#  SECTION:=============================================================
#            Class
#  =====================================================================


class VoicevoxAudioPlayer:
    """Class for text to speech by Voicevox"""

    def __init__(
        self,
        speaker: int,
        speed: float,
        pitch: float,
        intonation: float,
        volume: float,
        host: str,
        port: int,
    ):
        self.speaker = speaker
        self.speed = speed
        self.pitch = pitch
        self.intonation = intonation
        self.volume = volume
        self.base_url = f"http://{host}:{port}/"

    #  SECTION:=============================================================
    #            Functions, helper
    #  =====================================================================

    async def _generate_query(self, text: str) -> dict[str, dict] | None:
        params = {
            "text": text,
            "speaker": self.speaker,
        }

        try:
            async with httpx.AsyncClient() as client:
                query_response = await client.post(
                    f"{self.base_url}audio_query",
                    params=params,
                )
                query_response.raise_for_status()

                # Modify query_response by using self. parameters
                query_data = query_response.json()
                query_data["speedScale"] = self.speed
                query_data["witchScale"] = self.pitch
                query_data["intonationScale"] = self.intonation
                query_data["volumeScale"] = self.volume

                query = {"params": params, "json": query_data}
                # query = {"params": params, "json": json.dumps(query_data)}
                return query

        except httpx.HTTPStatusError as e:
            logger.error("HTTP error occurred:", e)
        except httpx.RequestError as e:
            logger.error("A request error occurred:", e)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

        return None

    async def _synthesize_audio(self, query: dict[str, dict]) -> bytes | None:
        try:
            async with httpx.AsyncClient() as client:
                synthesis = await client.post(
                    f"{self.base_url}synthesis",
                    headers={"Content-Type": "application/json"},
                    params=query["params"],
                    json=query["json"],
                )
            return synthesis.content

        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Error response {exc.response.status_code} while requesting {exc.request.url}"
            )
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url}: {exc}")
        except Exception as exc:
            logger.error(f"Unexpected error: {exc}")

        return None

    async def _play_audio(self, audio_binary: bytes) -> None:
        # Use BytesIO to treat bytes as a file object
        audio_io = io.BytesIO(audio_binary)

        # Open the audio bytes as a wave file
        with wave.open(audio_io, "rb") as wave_read:
            # Extract audio parameters
            audio_data = wave_read.readframes(wave_read.getnframes())
            num_channels = wave_read.getnchannels()
            bytes_per_sample = wave_read.getsampwidth()
            sample_rate = wave_read.getframerate()

        # Create a WaveObject from the audio data and parameters
        wave_obj = sa.WaveObject(
            audio_data, num_channels, bytes_per_sample, sample_rate
        )

        # Play the audio
        play_obj = wave_obj.play()
        # Await until the audio playback is done without blocking the event loop
        while play_obj.is_playing():
            await asyncio.sleep(0.1)

        # # Wait until playback is complete
        # play_obj.wait_done()

    def _generate_query_sync(self, text: str) -> dict[str, dict] | None:
        params = {
            "text": text,
            "speaker": self.speaker,
        }

        try:
            query_response = requests.post(
                f"{self.base_url}audio_query",
                params=params,
            )
            query_response.raise_for_status()

            # Modify query_response by using self. parameters
            query_data = query_response.json()
            query_data["speedScale"] = self.speed
            query_data["witchScale"] = self.pitch
            query_data["intonationScale"] = self.intonation
            query_data["volumeScale"] = self.volume

            query = {"params": params, "json": query_data}
            return query

        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error occurred:", e)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("A request error occurred:", e)
        except Exception as e:
            logger.error(f"Failed. error: {e}")

        return None

    def _synthesize_audio_sync(self, query: dict[str, dict]) -> bytes | None:
        try:
            synthesis = requests.post(
                f"{self.base_url}synthesis",
                headers={"Content-Type": "application/json"},
                params=query["params"],
                json=query["json"],
            )
            return synthesis.content

        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error occurred:", e)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("A request error occurred:", e)
        except Exception as e:
            logger.error(f"Failed. error: {e}")

        return None

    def _play_audio_sync(self, audio_binary: bytes) -> None:
        # Use BytesIO to treat bytes as a file object
        audio_io = io.BytesIO(audio_binary)

        # Open the audio bytes as a wave file
        with wave.open(audio_io, "rb") as wave_read:
            # Extract audio parameters
            audio_data = wave_read.readframes(wave_read.getnframes())
            num_channels = wave_read.getnchannels()
            bytes_per_sample = wave_read.getsampwidth()
            sample_rate = wave_read.getframerate()

        # Create a WaveObject from the audio data and parameters
        wave_obj = sa.WaveObject(
            audio_data, num_channels, bytes_per_sample, sample_rate
        )

        # Play the audio
        play_obj = wave_obj.play()
        # Wait until playback is complete
        play_obj.wait_done()

    #  SECTION:=============================================================
    #            Functions, Main
    #  =====================================================================

    async def say(self, text: str) -> None:
        query = await self._generate_query(text)
        audio = await self._synthesize_audio(query) if query else None
        if audio:
            await self._play_audio(audio)

    def configure(
        self,
        *,
        speaker: int | None = None,
        speed: float | None = None,
        pitch: float | None = None,
        intonation: float | None = None,
        volume: float | None = None,
    ) -> None:
        if speaker is not None:
            self.speaker = speaker
        if speed is not None:
            self.speed = speed
        if pitch is not None:
            self.pitch = pitch
        if intonation is not None:
            self.intonation = intonation
        if volume is not None:
            self.volume = volume


async def main():
    TEXT = "テストです"
    SPEAKER = 3
    SPEED = 1.0
    PITCH = 0.0
    INTONATION = 1.0
    VOLUME = 1.0

    logging.basicConfig(
        level=logging.DEBUG,
    )
    voicevox_player = VoicevoxAudioPlayer(
        speaker=SPEAKER,
        speed=SPEED,
        pitch=PITCH,
        intonation=INTONATION,
        volume=VOLUME,
        host="localhost",
        port=50021,
    )

    await voicevox_player.say(TEXT)

    voicevox_player.configure(speaker=14)
    await voicevox_player.say(TEXT)


if __name__ == "__main__":
    asyncio.run(main())
