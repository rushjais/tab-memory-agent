import cartesia
from dotenv import load_dotenv
import os

load_dotenv()

cartesia_client = cartesia.Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))

def speak_reminder(message: str) -> bytes:
    voice = next(iter(cartesia_client.voices.list()))

    audio_chunks = []
    for chunk in cartesia_client.tts.bytes(
        model_id="sonic-2",
        transcript=message,
        voice={"mode": "id", "id": voice.id},
        output_format={
            "container": "wav",
            "encoding": "pcm_f32le",
            "sample_rate": 44100
        }
    ):
        audio_chunks.append(chunk)

    return b"".join(audio_chunks)