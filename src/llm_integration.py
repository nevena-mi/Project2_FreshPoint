"""
llm_integration.py — Thin wrapper around the LLM client.

Uses python-dotenv + the OpenAI() client, which reads OPENAI_API_KEY from
the environment automatically (no need to pass api_key= manually).
"""

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

DEFAULT_MODEL = "gpt-4o-mini"


def complete(prompt: str, model: str = DEFAULT_MODEL, temperature: float = 0.7) -> str:
    """Send a single prompt and return the text response."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()
