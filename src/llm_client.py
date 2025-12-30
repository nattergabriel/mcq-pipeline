"""
Provides a client to interact with an OpenAI-compatible Large Language Model API using LangChain.
"""

import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


load_dotenv()


def get_llm_model(model: str, temperature: float) -> ChatOpenAI:
    """
    Returns a configured ChatOpenAI instance using environment variables.
    Includes retry logic for rate limit errors (429).
    """
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not base_url or not api_key:
        raise ValueError("Base URL or token not set in .env file.")

    logger.debug(
        f"Creating ChatOpenAI with model: {model}, temperature: {temperature}")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
        max_retries=20,
        timeout=120
    )
