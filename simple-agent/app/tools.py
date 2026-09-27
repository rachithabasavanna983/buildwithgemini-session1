# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.cloud import firestore

# Hardcode project ID explicitly to prevent Agent Engine from returning project number
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-5ae45ab25a38"


def get_firestore_client():
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def list_pantry_items(category: str = "") -> str:
    """Lists items from the pantry. Optionally filter by category.

    Args:
        category: Optional category filter (e.g. Produce, Dairy, Grains, Canned Goods, Spices).
            If empty, all items are returned.

    Returns:
        A list of pantry items with their quantity, unit, category, and expiration date.
    """
    db = get_firestore_client()
    query = db.collection("pantry_items")
    if category:
        query = query.where("category", "==", category)
    docs = query.stream()

    items = []
    for doc in docs:
        data = doc.to_dict()
        items.append(
            f"- {data.get('name')}: {data.get('quantity')} {data.get('unit')} "
            f"(Category: {data.get('category')}, Expires: {data.get('expiration_date', 'N/A')})"
        )

    if not items:
        return "No pantry items found."
    return "Pantry Items:\n" + "\n".join(items)


def add_pantry_item(
    name: str,
    category: str,
    quantity: float,
    unit: str,
    expiration_date: str = "",
    notes: str = "",
) -> str:
    """Adds a new item to the pantry inventory or updates an existing item.

    Args:
        name: Name of the pantry item (e.g. Milk, Eggs, Olive Oil).
        category: Category of the item (e.g. Produce, Dairy, Grains, Canned Goods, Spices).
        quantity: Quantity count or amount.
        unit: Unit of measurement (e.g. items, cups, lbs, oz, liters, cartons).
        expiration_date: Optional expiration date in YYYY-MM-DD format.
        notes: Optional storage notes or brand information.

    Returns:
        Confirmation message.
    """
    db = get_firestore_client()
    doc_id = name.lower().replace(" ", "_")
    doc_ref = db.collection("pantry_items").document(doc_id)
    doc_ref.set({
        "name": name,
        "category": category,
        "quantity": quantity,
        "unit": unit,
        "expiration_date": expiration_date,
        "notes": notes,
    })
    return f"Successfully added '{name}' ({quantity} {unit}) under category '{category}' to the pantry."


def update_item_quantity(name: str, quantity: float) -> str:
    """Updates the quantity of an existing item in the pantry.

    Args:
        name: Name of the pantry item.
        quantity: New quantity amount.

    Returns:
        Confirmation message.
    """
    db = get_firestore_client()
    doc_id = name.lower().replace(" ", "_")
    doc_ref = db.collection("pantry_items").document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        return f"Item '{name}' not found in pantry."
    doc_ref.update({"quantity": quantity})
    return f"Updated quantity of '{name}' to {quantity}."


RECIPE_CATALOG = [
    {
        "name": "Classic Scrambled Eggs & Rice",
        "category": "Breakfast",
        "ingredients": ["Organic Eggs", "Jasmine Rice", "Olive Oil"],
        "instructions": "Whisk eggs, scramble in hot pan with olive oil, serve warm over freshly steamed Jasmine rice.",
    },
    {
        "name": "Rustic Tomato Rice Soup",
        "category": "Soup",
        "ingredients": ["Canned Diced Tomatoes", "Jasmine Rice", "Olive Oil"],
        "instructions": "Simmer diced tomatoes with water and olive oil, fold in cooked Jasmine rice, season with salt and pepper.",
    },
    {
        "name": "Creamy Avocado Omelet",
        "category": "Breakfast",
        "ingredients": ["Organic Eggs", "Avocado", "Olive Oil"],
        "instructions": "Whisk eggs, pour into skillet with olive oil, fold sliced avocados inside when almost set.",
    },
    {
        "name": "Caprese Salad",
        "category": "Salad",
        "ingredients": ["Olive Oil", "Canned Diced Tomatoes", "Mozzarella", "Basil"],
        "instructions": "Slice tomatoes, layer with cheese and basil, and drizzle with extra virgin olive oil.",
    },
]


def suggest_recipes(available_ingredients: str = "") -> str:
    """Suggests recipes based on available pantry ingredients.

    Args:
        available_ingredients: Optional comma-separated list of ingredients.
            If empty, current pantry inventory is queried from Firestore automatically.

    Returns:
        A list of recipe suggestions matching current ingredients.
    """
    if not available_ingredients:
        db = get_firestore_client()
        docs = db.collection("pantry_items").stream()
        pantry_names = [doc.to_dict().get("name", "").lower() for doc in docs]
    else:
        pantry_names = [i.strip().lower() for i in available_ingredients.split(",")]

    matched = []
    for recipe in RECIPE_CATALOG:
        required = [ing.lower() for ing in recipe["ingredients"]]
        have = [ing for ing in required if any(p in ing or ing in p for p in pantry_names)]
        missing = [recipe["ingredients"][i] for i, ing in enumerate(required) if ing not in have]

        if len(have) > 0:
            matched.append(
                f"🍲 {recipe['name']} ({recipe['category']})\n"
                f"   - Available Ingredients: {len(have)}/{len(required)}\n"
                f"   - Missing Ingredients: {', '.join(missing) if missing else 'None! You have everything!'}\n"
                f"   - Instructions: {recipe['instructions']}"
            )

    if not matched:
        return "No recipe suggestions found for the current ingredients."

    return "Recipe Suggestions:\n\n" + "\n\n".join(matched)


import json
import os
import urllib.parse
import urllib.request


def search_online_recipes(query: str) -> str:
    """Searches live online recipes using TheMealDB API.

    Args:
        query: Recipe name or main ingredient to search for (e.g. Chicken, Pasta, Rice, Soup).

    Returns:
        A list of matching online recipes with category, cuisine area, ingredients, and instructions.
    """
    api_key = os.getenv("THEMEALDB_API_KEY", "1")
    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SmartPantryAgent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        meals = data.get("meals")
        if not meals:
            return f"No online recipes found matching query '{query}'."

        results = []
        for meal in meals[:3]:  # Top 3 results
            name = meal.get("strMeal", "Unknown")
            category = meal.get("strCategory", "General")
            area = meal.get("strArea", "International")
            instructions = meal.get("strInstructions", "").strip()

            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                measure = meal.get(f"strMeasure{i}")
                if ing and ing.strip():
                    ing_str = (
                        f"{measure.strip()} {ing.strip()}"
                        if measure and measure.strip()
                        else ing.strip()
                    )
                    ingredients.append(ing_str)

            ing_list = ", ".join(ingredients[:8]) + ("..." if len(ingredients) > 8 else "")
            short_instructions = (
                (instructions[:180] + "...") if len(instructions) > 180 else instructions
            )

            results.append(
                f"🌐 {name} ({category} - {area})\n"
                f"   - Key Ingredients: {ing_list}\n"
                f"   - Instructions: {short_instructions}"
            )

        return "Online Recipe Results:\n\n" + "\n\n".join(results)

    except Exception as e:
        return f"Error querying online recipe database: {str(e)}"


def geocode_address(address: str) -> str:
    """Converts a physical address or city name into geographic coordinates (latitude, longitude).

    Args:
        address: The address, city, or landmark string to geocode (e.g. "San Francisco, CA").

    Returns:
        Formatted address, latitude, and longitude.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key or api_key == "PASTE_KEY_HERE":
        return "Error: GOOGLE_MAPS_API_KEY is not configured in .env."

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SmartPantryAgent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        status = data.get("status")
        if status != "OK" or not data.get("results"):
            return f"Geocoding failed for '{address}'. Status: {status}"

        result = data["results"][0]
        formatted_address = result.get("formatted_address", address)
        loc = result["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]

        return (
            f"📍 Geocoded Result:\n"
            f"   - Address: {formatted_address}\n"
            f"   - Location: Latitude {lat}, Longitude {lng}"
        )

    except Exception as e:
        return f"Error performing geocoding request: {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "supermarket",
    radius_meters: float = 5000.0,
) -> str:
    """Finds nearby places of a given type around coordinates using the Places API (New).

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Place type to filter (e.g. supermarket, grocery_store, restaurant, bakery).
        radius_meters: Search radius in meters (default 5000m).

    Returns:
        A list of nearby places with their display name, address, and location coordinates.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key or api_key == "PASTE_KEY_HERE":
        return "Error: GOOGLE_MAPS_API_KEY is not configured in .env."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }

    body = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius_meters,
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        places = data.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found within {radius_meters}m."

        results = []
        for place in places:
            display_name = place.get("displayName", {}).get("text", "Unknown Place")
            formatted_address = place.get("formattedAddress", "No address available")
            loc = place.get("location", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")

            results.append(
                f"🏬 **{display_name}**\n"
                f"   - Address: {formatted_address}\n"
                f"   - Location: ({lat}, {lng})"
            )

        return f"Nearby Places ({place_type}):\n\n" + "\n\n".join(results)

    except Exception as e:
        return f"Error performing Places API (New) search: {str(e)}"


import base64
import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

GCS_BUCKET_NAME = "smart-pantry-images-qwiklabs-gcp-03-5ae45ab25a38"


def generate_item_image(item_name: str, tool_context: ToolContext = None) -> str:
    """Generates an image for a pantry item or recipe dish using Gemini 3.1 Flash Lite Image.

    Saves the image as an artifact in the Playground panel and uploads it to Cloud Storage.

    Args:
        item_name: Name or description of the item/dish to generate an image for (e.g. "Caprese Salad", "Organic Eggs").
        tool_context: Optional ADK ToolContext provided automatically by the runtime.

    Returns:
        Confirmation message containing the public HTTPS Cloud Storage URL of the generated image.
    """
    try:
        # 1. Initialize Gemini Client for global region Vertex AI
        genai_client = genai.Client(
            vertexai=True,
            project=FIRESTORE_PROJECT_ID,
            location="global",
        )

        prompt = (
            f"A vibrant, professional high-quality food photography photo of {item_name} on a clean wooden table."
        )
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )

        image_bytes = None
        mime_type = "image/jpeg"
        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
        ):
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not image_bytes:
            return f"Failed to generate image for '{item_name}': No image data returned from model."

        # 2. Save artifact to Playground via tool_context if available
        safe_item_name = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in item_name.lower()
        )
        filename = f"{safe_item_name}_{uuid.uuid4().hex[:6]}.jpg"

        if tool_context and hasattr(tool_context, "save_artifact"):
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 3. Upload bytes to public Cloud Storage bucket
        gcs_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return (
            f"🎨 Generated image for '{item_name}' successfully!\n"
            f"   - Saved to Playground Artifacts as: {filename}\n"
            f"   - Public Cloud Storage URL: {public_url}"
        )

    except Exception as e:
        return f"Error generating item image: {str(e)}"


def generate_item_video(item_name: str, tool_context: ToolContext = None) -> str:
    """Generates a short video for a pantry item or recipe dish using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the video as an artifact in the Playground panel and uploads it to Cloud Storage.

    Args:
        item_name: Name or description of the item/dish to generate a video for (e.g. "Caprese Salad", "Organic Eggs").
        tool_context: Optional ADK ToolContext provided automatically by the runtime.

    Returns:
        Confirmation message containing the public HTTPS Cloud Storage URL of the generated video.
    """
    try:
        # 1. Initialize Gemini Client for global region Vertex AI
        genai_client = genai.Client(
            vertexai=True,
            project=FIRESTORE_PROJECT_ID,
            location="global",
        )

        prompt = f"A short 3 to 5 second cinematic video clip showing {item_name} being prepared or displayed on a clean kitchen counter."
        interaction = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        video_bytes = None
        mime_type = "video/mp4"
        if hasattr(interaction, "output_video") and interaction.output_video:
            data = interaction.output_video.data
            if isinstance(data, str):
                video_bytes = base64.b64decode(data)
            elif isinstance(data, bytes):
                video_bytes = data

        if not video_bytes:
            return f"Failed to generate video for '{item_name}': No video data returned from model."

        # 2. Save artifact to Playground via tool_context if available
        safe_item_name = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in item_name.lower()
        )
        filename = f"{safe_item_name}_{uuid.uuid4().hex[:6]}.mp4"

        if tool_context and hasattr(tool_context, "save_artifact"):
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 3. Upload bytes to public Cloud Storage bucket
        gcs_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return (
            f"🎬 Generated video for '{item_name}' successfully!\n"
            f"   - Saved to Playground Artifacts as: {filename}\n"
            f"   - Public Cloud Storage URL: {public_url}"
        )

    except Exception as e:
        return f"Error generating item video: {str(e)}"





