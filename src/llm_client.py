"""
Provides a client to interact with an OpenAI-compatible Large Language Model API.
"""

import os
from openai import OpenAI, APIError
from typing import Optional
from dotenv import load_dotenv


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
        base_url = os.getenv("AQUEDUCT_BASE_URL")
        api_key = os.getenv("AQUEDUCT_TOKEN")

        if not base_url or not api_key:
            raise ValueError("Base URL or token not set in .env file.")

        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key)

    def call_llm(self, system_message: str, user_message: str, model: str, temperature: float = 0.5) -> Optional[str]:
        """
        Sends a request to the LLM and returns the response content.
        """
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature)

            return response.choices[0].message.content
        except APIError as e:
            print(f"The API returned an error: {e}")
