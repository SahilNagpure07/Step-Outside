import io, os, random
from PIL import Image

MODELS = list(dict.fromkeys([
    os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it"),
    "gemma-4-31b-it",
]))

FALLBACK_CHALLENGES = [
    "Find something alive growing somewhere unusual.",
    "Find something older than you that still works.",
    "Find the smallest piece of nature near you.",
    "Find a shadow doing something interesting.",
    "Find something that moves on its own.",
]


def shrink(image_bytes):
    """Make the photo small (faster upload, faster answer) and make sure it is a JPEG."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image.thumbnail((768, 768))
    output = io.BytesIO()
    image.save(output, "JPEG", quality=80)
    return output.getvalue()


def ask_gemma(prompt, image_bytes=None):
    """Send a prompt (and optional photo) to Gemma. Returns text or None."""
    if not os.getenv("GEMINI_API_KEY"):
        return None

    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),
        http_options=types.HttpOptions(timeout=30000),
    )
    parts = [prompt]
    if image_bytes:
        parts.insert(0, types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

    for model in MODELS:
        try:
            result = client.models.generate_content(model=model, contents=parts)
            print("Answered by:", model)
            return (result.text or "").strip() or None
        except Exception as error:
            print(f"{model} failed:", error)
    return None


def make_challenge(old_challenges):
    prompt = (
        "Write ONE short challenge (max 12 words) that makes someone go outside "
        "and look at the real world. No emojis. "
        f"Do not repeat these: {old_challenges}"
    )
    text = ask_gemma(prompt)
    if text:
        return text.split("\n")[0]
    return random.choice(FALLBACK_CHALLENGES)


def react_to_photo(challenge, image_bytes):
    """Returns (reply, subject). Reply is one short sentence."""
    try:
        image_bytes = shrink(image_bytes)
    except Exception as error:
        print("Could not read image:", error)
        return "That's a real thing, in the real world.", ""

    prompt = (
        f'The challenge was: "{challenge}". Look at the photo. Answer in exactly two lines:\n'
        "SUBJECT: <what the photo mainly shows, 1-3 words>\n"
        "REPLY: <one short, calm sentence about what you see. "
        "Do NOT judge whether it matches the challenge. Never say it is wrong.>"
    )
    text = ask_gemma(prompt, image_bytes)
    if text and "REPLY:" in text:
        subject = text.split("SUBJECT:")[1].split("\n")[0].strip() if "SUBJECT:" in text else ""
        reply = text.split("REPLY:")[1].strip().split("\n")[0]
        return reply, subject
    return "That's a real thing, in the real world.", ""
