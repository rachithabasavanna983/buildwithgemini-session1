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

# Explicit hardcoded project ID
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-5ae45ab25a38"

SAMPLE_ITEMS = [
    {
        "name": "Olive Oil",
        "category": "Pantry Staples",
        "quantity": 1,
        "unit": "bottle",
        "expiration_date": "2027-06-30",
        "notes": "Extra virgin cold-pressed olive oil",
    },
    {
        "name": "Whole Milk",
        "category": "Dairy",
        "quantity": 2,
        "unit": "cartons",
        "expiration_date": "2026-10-05",
        "notes": "Organic 2% milk",
    },
    {
        "name": "Jasmine Rice",
        "category": "Grains",
        "quantity": 5,
        "unit": "lbs",
        "expiration_date": "2027-12-01",
        "notes": "Long grain aromatic rice",
    },
    {
        "name": "Organic Eggs",
        "category": "Dairy",
        "quantity": 12,
        "unit": "items",
        "expiration_date": "2026-10-15",
        "notes": "Grade A large eggs",
    },
    {
        "name": "Canned Diced Tomatoes",
        "category": "Canned Goods",
        "quantity": 4,
        "unit": "cans",
        "expiration_date": "2027-04-15",
        "notes": "Fire-roasted diced tomatoes",
    },
]


def seed():
    print(f"Connecting to Firestore project '{FIRESTORE_PROJECT_ID}'...")
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    collection_ref = db.collection("pantry_items")

    for item in SAMPLE_ITEMS:
        doc_id = item["name"].lower().replace(" ", "_")
        collection_ref.document(doc_id).set(item)
        print(f"Seeded: {item['name']} ({item['quantity']} {item['unit']})")

    print("\n✅ Firestore successfully seeded with pantry items!")


if __name__ == "__main__":
    seed()
