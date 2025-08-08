"""This module provides a Translator class for translating text.

The Translator class encapsulates the logic for translating text using different APIs.

Examples:

  translator = Translator(source_lang="en", target_lang="ja")
  result_dict = await translator.translate_as_dict("Hello, world!")
  print("Dict result:", result_dict)

  result_json = await translator.translate_as_json("Hello, world!")
  print("JSON result:", result_json)k
"""

import json
import httpx
import logging

from config import Urls

#  SECTION:=============================================================
#            Logger
#  =====================================================================

logger = logging.getLogger(__name__)


#  SECTION:=============================================================
#            Class
#  =====================================================================


class Translator:
    """Class for translating text using different APIs."""

    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        api_type: str = "gas",
        result_type: str = "translated",
        # api_key: str | None = None,
    ):
        """Initialize the Translator object with language settings and API type."""
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.api_type = api_type
        self.result_type = result_type
        # self.api_key = api_key

        # Settings for each API
        if self.api_type == "gas":
            self.base_url = Urls.GAS_BASE_URL
        else:
            raise ValueError("Unsupported API type")

    #  SECTION:=============================================================
    #            Functions, helper
    #  =====================================================================

    def _make_result_dict(
        self, original_text: str, translated_text: str | None
    ) -> dict:
        """Create a dictionary with translation data."""
        return {
            "translated_text": translated_text,
            "original_text": original_text,
            "source_language": self.source_lang,
            "target_language": self.target_lang,
            "type": self.result_type,
        }

    #  SECTION:=============================================================
    #            Functions
    #  =====================================================================

    async def call_api(self, text: str) -> str | None:
        """Call the underlying translation API and return the translated text.

        Args:
          text (str): The text to translate.
        Returns:
          str: The translated text or None if the API call fails.
        """
        # API: gas, google application script returns a text that is translated.
        # The parameters: original text, source lang, target lang.
        if self.api_type == "gas":
            params = {
                "text": text,
                "source": self.source_lang.lower(),
                "target": self.target_lang.lower(),
            }
            try:
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.get(self.base_url, params=params)
                    response.raise_for_status()
                    return response.text
            except httpx.HTTPError as e:
                logger.error(f"HTTP request failed: {e}")
                return None
            except Exception as e:
                logger.error(f"API request failed: {e}")
                return None
        else:
            raise ValueError("Unsupported API type")

    def to_json(self, original_text: str, translated_text: str | None) -> str:
        """
        Serialize the translation result dictionary to a JSON string.

        Args:
            original_text (str): The original text.
            translated_text (str): The translated text or None.

        Returns:
            str: The JSON string representation of the translation result dictionary.
        """
        result = self._make_result_dict(original_text, translated_text)
        return json.dumps(result, ensure_ascii=False)

    async def translate_as_json(self, text: str) -> str:
        """
        Translate text and return the result as a JSON string.

        Args:
            text (str): The text to translate.

        Returns:
            str: The JSON string representation of the translation result dictionary.
        """
        translated_text = await self.call_api(text)
        return self.to_json(text, translated_text)

    async def translate_as_dict(self, text: str) -> dict:
        """
        Translate text and return the result as a Python dictionary.

        Args:
            text (str): The text to translate.

        Returns:
            dict: The translation result dictionary.
        """
        translated_text = await self.call_api(text)
        return self._make_result_dict(text, translated_text)


# =================
# Usage examples
# =================

import asyncio


async def main():
    translator = Translator(source_lang="en", target_lang="ja")

    # Get result as dictionary
    result_dict = await translator.translate_as_dict("Hello, world!")
    print("Dict result:", result_dict)

    # Get result as JSON string
    result_json = await translator.translate_as_json("Hello, world!")
    print("JSON result:", result_json)


if __name__ == "__main__":
    asyncio.run(main())
