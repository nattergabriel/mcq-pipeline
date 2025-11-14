"""
Provides a client to interact with an OpenAI-compatible Large Language Model API.
"""

import os
import logging
from openai import OpenAI, APIError
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class LLMClient:
    """
    A client for making calls to an OpenAI-compatible LLM.
    """

    def __init__(self):
        """
        Initializes the LLMClient by loading environment variables and
        setting up the API client.
        """
        load_dotenv()
        base_url = os.getenv("OPENAI_BASE_URL")
        api_key = os.getenv("OPENAI_API_KEY")

        if not base_url or not api_key:
            raise ValueError("Base URL or token not set in .env file.")

        self._client = OpenAI(base_url, api_key)

    def call_llm(self, system_message: str, user_message: str, model: str, temperature: float = 0.5) -> Optional[str]:
        """
        Sends a request to the LLM and returns the response content.
        """
        logger.debug(
            f"Calling LLM with model: {model}, temperature: {temperature}")
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature)

            logger.debug("LLM call successful")
            return response.choices[0].message.content
        except APIError as e:
            logger.error(f"API error: {e}")
            return None
