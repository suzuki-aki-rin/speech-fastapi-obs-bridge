import json
import requests

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

    def call_api(self, text: str) -> str:
        if self.api_type == "gas":
            params = {
                "text": text,
                "source": self.source_lang.lower(),
                "target": self.target_lang.lower(),
            }
            response = requests.get(self.base_url, params=params)
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

    def translate(self, text: str) -> str:
        translated_text = self.call_api(text)
        return self.to_json(text, translated_text)


def main():
    translator = Translator("ja", "en")
    json_result = translator.translate("こんにちは、初めまして")
    print(json_result)


if __name__ == "__main__":
    main()


#
# # Translate text with Google app script
# def translate_text_by_GAS(
#     text: str,
#     source_lang: str,
#     target_lang: str,
#     base_url: str = Urls.TRASLATOR_BASE_URL,
# ) -> str | None:
#     query_params = {
#         "text": text,
#         "source": source_lang,
#         "target": target_lang,
#     }
#     try:
#         response = requests.get(url=base_url, params=query_params)
#         response.raise_for_status()
#         # This API return plain/text
#         return response.text
#
#     except Exception as e:
#         print(f"some exception: {e}")
#
#
# # Translate text from source lang to target lang. wrapper
# def translate_text(text: str, source_lang: str, target_lang: str) -> str | None:
#     return (
#         translate_text_by_GAS(
#             text=text, source_lang=source_lang, target_lang=target_lang
#         )
#         or None
#     )
