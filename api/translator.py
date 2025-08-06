import json
import httpx
import asyncio

from config import Urls


class Translator:
    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        api_type: str = "gas",
        result_type: str = "translated",
        # api_key: str | None = None,
    ):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.api_type = api_type
        self.result_type = result_type
        # self.api_key = api_key

        # APIごとのベースURLやパラメーター設定
        if self.api_type == "gas":
            self.base_url = Urls.GAS_BASE_URL
        else:
            raise ValueError("Unsupported API type")

    async def call_api(self, text: str) -> str:
        if self.api_type == "gas":
            params = {
                "text": text,
                "source": self.source_lang.lower(),
                "target": self.target_lang.lower(),
            }
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                return response.text
        else:
            raise ValueError("Unsupported API type")

    def to_json(self, original_text: str, translated_text: str) -> str:
        result = {
            "text": translated_text,
            "source_language": self.source_lang,
            "target_language": self.target_lang,
            "type": self.result_type,
        }
        return json.dumps(result, ensure_ascii=False)

    async def translate(self, text: str) -> str:
        translated_text = await self.call_api(text)
        return self.to_json(text, translated_text)


async def main():
    # Create a Translator instance with source and target languages
    translator = Translator(source_lang="en", target_lang="ja")

    # Text to translate
    text_to_translate = "Hello, how are you?"

    # Call the async translate method
    translated_json = await translator.translate(text_to_translate)

    # Print the JSON result
    print("Translation result:", translated_json)


if __name__ == "__main__":
    asyncio.run(main=main())
