import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


client = OpenAI(
    base_url=os.getenv("AQUEDUCT_BASE_URL"),
    api_key=os.getenv("AQUEDUCT_TOKEN"),
)


def call_llm(system_message: str, user_message: str, model: str) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        print(e)
        return ""
