import os

try:
    from groq import Groq
except ImportError:
    Groq = None

def get_groq_client():
    """Initialize Groq client using environment variable."""
    if Groq is None:
        raise ImportError("The 'groq' package is not installed.")
        
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")
    return Groq(api_key=api_key)

def call_groq_model(messages: list[dict], model: str = "llama-3.3-70b-versatile", temperature: float = 0.0) -> str:
    """Make a call to Groq API and return the text content."""
    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Groq API call failed: {e}")
