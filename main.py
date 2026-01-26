# Trigger Test 1
import os
from google.cloud import bigquery

PROJECT_ID = "project-36a10255-b110-4164-8f8"
TABLE_ID = f"{PROJECT_ID}.30_verse.video_metadata"
VIDEO_ID = os.getenv("VIDEO_ID")

print(f"🔍 Testing access for VIDEO_ID: {VIDEO_ID}")

client = bigquery.Client(project=PROJECT_ID)
query = f"SELECT * FROM `{TABLE_ID}` WHERE video_id = {VIDEO_ID}"

try:
    results = list(client.query(query).result())
    if results:
        row = results[0]
        print(f"✅ SUCCESS: Found {row.bible_verse}")
        print(f"📖 Text: {row.bible_quote}")
    else:
        print(f"❌ ERROR: ID {VIDEO_ID} not found in BigQuery.")
except Exception as e:
    print(f"❌ Database Error: {e}")
