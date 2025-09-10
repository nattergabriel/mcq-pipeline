"""
Provides a client to interact with an OpenAI-compatible Large Language Model API.
"""

import os
from openai import OpenAI
from typing import Optional
from dotenv import load_dotenv


class LLMClient:
    """A client for making calls to an OpenAI-compatible LLM."""

    def __init__(self):
        """Initializes the LLMClient and sets up the API client."""
        load_dotenv()
        base_url = os.getenv("AQUEDUCT_BASE_URL")
        api_key = os.getenv("AQUEDUCT_TOKEN")

        if not base_url or not api_key:
            raise ValueError("Base URL or token not set in .env file.")

        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

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
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")


def main():
    """
    An example function to test the LLMClient class.
    """
    try:
        llm_api_client = LLMClient()

        system_prompt = "you are an expert in..."
        user_prompt = "hi how are you?"
        model = "mistral-small-3.1-24b"

        llm_response = llm_api_client.call_llm(
            system_message=system_prompt,
            user_message=user_prompt,
            model=model,
            temperature=0.7
        )

        if llm_response:
            print(llm_response)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
