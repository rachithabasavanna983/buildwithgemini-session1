import base64
import sys
import traceback
from google import genai

FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-5ae45ab25a38"

print("Initializing client...")
client = genai.Client(
    vertexai=True,
    project=FIRESTORE_PROJECT_ID,
    location="global",
)

print("Calling client.interactions.create...")
sys.stdout.flush()

try:
    interaction = client.interactions.create(
        model="gemini-omni-flash-preview",
        input="A short 3 second video showing fresh green apples on a wooden kitchen table.",
    )
    print("SUCCESS! Interaction:", interaction)
    print("Attributes:", dir(interaction))
    if hasattr(interaction, "output_video") and interaction.output_video:
        print("Output video:", interaction.output_video)
        print("Data type:", type(interaction.output_video.data))
except Exception as e:
    print("ERROR:")
    traceback.print_exc()

sys.stdout.flush()
