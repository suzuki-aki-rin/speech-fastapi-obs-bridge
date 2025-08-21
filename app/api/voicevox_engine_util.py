import asyncio
import json
import tempfile
import logging

import httpx
import requests

# import pyaudio
import simpleaudio as sa

from app.config.app_config import app_config

# VOICEVOX_FEMALE, VOICEVOX_HOST, VOICEVOX_MALE, VOICEVOX_PORT


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

TEXT = "テストです"
SPEAKER = 3
SPEED = 1.0
PITCH = 0.0
INTONATION = 1.0
VOLUME = 1.0

VOICEVOX_BASE_URL = (
    f"http://{app_config.voicevox.server.host}:{app_config.voicevox.server.port}/"
)


def voicevox_engine_say(
    text=TEXT,
    speaker=SPEAKER,
    speed=SPEED,
    pitch=PITCH,
    intonation=INTONATION,
    volume=VOLUME,
):
    # 音声化する文言と話者を指定(3で標準ずんだもんになる)
    params = (
        ("text", text),
        ("speaker", speaker),
    )

    # 音声合成用のクエリ作成
    # エンジン起動時に表示されているIP、portを指定
    try:
        query_response = requests.post(
            f"{VOICEVOX_BASE_URL}audio_query",
            params=params,
        )
    except:
        print("----- Failed to connect to voicevox server ----- ")
        return
        # raise SystemExit("EXIT ----- Failed to connect to voicevox server ----- ")

    query_response.raise_for_status()
    # speedScale': 1.0, 'pitchScale': 0.0, 'intonationScale': 1.0, 'volumeScale': 1
    query_data = query_response.json()
    query_data["speedScale"] = speed
    query_data["witchScale"] = pitch
    query_data["intonationScale"] = intonation
    query_data["volumeScale"] = volume

    # 音声合成を実施
    synthesis = requests.post(
        f"{VOICEVOX_BASE_URL}synthesis",
        headers={"Content-Type": "application/json"},
        params=params,
        data=json.dumps(query_data),
    )

    # 再生処理
    voice = synthesis.content
    # pya = pyaudio.PyAudio()
    #
    # # サンプリングレートが24000以外だとずんだもんが高音になったり低音になったりする
    # stream = pya.open(format=pyaudio.paInt16,
    #                   channels=1,
    #                   rate=24000,
    #                   output=True)
    #
    # stream.write(voice)
    # stream.stop_stream()
    # stream.close()
    # pya.terminate()

    with tempfile.NamedTemporaryFile(delete=True) as tf:
        tf.write(voice)
        # play_obj = simpleaudio.play_buffer(voice, 1, 2, 24000)
        wave_obj = sa.WaveObject.from_wave_file(tf.name)
        play_obj = wave_obj.play()
        play_obj.wait_done()


def voicevox_say_male(_text=TEXT):
    voicevox_engine_say(
        text=_text,
        speaker=app_config.voicevox.male_voice.speaker,
        speed=app_config.voicevox.male_voice.speed,
        pitch=app_config.voicevox.male_voice.pitch,
        intonation=app_config.voicevox.male_voice.intonation,
        volume=app_config.voicevox.male_voice.volume,
    )


def voicevox_say_female(_text=TEXT):
    voicevox_engine_say(
        text=_text,
        speaker=app_config.voicevox.female_voice.speaker,
        speed=app_config.voicevox.female_voice.speed,
        pitch=app_config.voicevox.female_voice.pitch,
        intonation=app_config.voicevox.female_voice.intonation,
        volume=app_config.voicevox.female_voice.volume,
    )


async def voicevox_engine_say_async(
    text=TEXT,
    speaker=SPEAKER,
    speed=SPEED,
    pitch=PITCH,
    intonation=INTONATION,
    volume=VOLUME,
):
    params = (
        ("text", text),
        ("speaker", speaker),
    )
    async with httpx.AsyncClient() as client:
        query_response = await client.post(
            f"{VOICEVOX_BASE_URL}audio_query", params=params
        )
        query_response.raise_for_status()
        query_data = query_response.json()
        # Modify query_data...
        synthesis = await client.post(
            f"{VOICEVOX_BASE_URL}synthesis",
            headers={"Content-Type": "application/json"},
            params=params,
            data=json.dumps(query_data),
        )
        voice = synthesis.content
    with tempfile.NamedTemporaryFile(delete=True) as tf:
        tf.write(voice)
        # play_obj = simpleaudio.play_buffer(voice, 1, 2, 24000)
        wave_obj = sa.WaveObject.from_wave_file(tf.name)
        play_obj = wave_obj.play()
        play_obj.wait_done()


async def voicevox_say_male_async(_text=TEXT):
    await voicevox_engine_say_async(
        text=_text,
        speaker=app_config.voicevox.male_voice.speaker,
        speed=app_config.voicevox.male_voice.speed,
        pitch=app_config.voicevox.male_voice.pitch,
        intonation=app_config.voicevox.male_voice.intonation,
        volume=app_config.voicevox.male_voice.volume,
    )


async def voicevox_say_female_async(_text=TEXT):
    await voicevox_engine_say_async(
        text=_text,
        speaker=app_config.voicevox.female_voice.speaker,
        speed=app_config.voicevox.female_voice.speed,
        pitch=app_config.voicevox.female_voice.pitch,
        intonation=app_config.voicevox.female_voice.intonation,
        volume=app_config.voicevox.female_voice.volume,
    )


async def main():
    task1 = asyncio.create_task(voicevox_engine_say_async(text="Hello"))
    task2 = asyncio.create_task(voicevox_engine_say_async(text="World"))
    await asyncio.gather(task1, task2)
    await voicevox_say_female_async(_text="こんにちは")


if __name__ == "__main__":
    # text = "こんにちは。私の名前はずんだもんです。"
    # # voicevox_engine_say(text, speaker=14, speed=2.0)
    # voicevox_say_male(text)
    # voicevox_say_female(text)
    asyncio.run(main())
