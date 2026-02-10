import os
from google.cloud import bigquery, storage
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip

# Configuration
PROJECT_ID = "project-36a10255-b110-4164-8f8"
RAW_BUCKET_NAME = "project-raw-assets"
OUTPUT_BUCKET_NAME = "project-tempe-processing"
VIDEO_ID = os.getenv("VIDEO_ID")

def assemble_video():
    if not VIDEO_ID:
        print("❌ ERROR: No VIDEO_ID environment variable found.")
        return

    print(f"🚀 Starting assembly for VIDEO_ID: {VIDEO_ID}")
    
    # Initialize Clients
    bq_client = bigquery.Client(project=PROJECT_ID)
    storage_client = storage.Client(project=PROJECT_ID)
    raw_bucket = storage_client.bucket(RAW_BUCKET_NAME)
    output_bucket = storage_client.bucket(OUTPUT_BUCKET_NAME)

    # 1. Fetch Latest Metadata from BigQuery
    query = f"""
        SELECT bible_quote FROM `{PROJECT_ID}.30_verse.video_metadata` 
        WHERE video_id = {VIDEO_ID} 
        AND status = 'pending'
        ORDER BY created_at DESC LIMIT 1
    """
    results = list(bq_client.query(query).result())
    if not results:
        print(f"❌ ERROR: Pending record for ID {VIDEO_ID} not found in BigQuery.")
        return
    
    bible_quote = results[0].bible_quote

    # 2. Download Video Assets from Folders (video_1, video_2, video_3)
    video_paths = []
    for i in range(1, 4):
        prefix = f"video_{i}/"
        blobs = storage_client.list_blobs(RAW_BUCKET_NAME, prefix=prefix)
        for blob in blobs:
            if blob.name.endswith(".mp4"):
                local_path = f"temp_video_{i}.mp4"
                blob.download_to_filename(local_path)
                video_paths.append(local_path)
                print(f"✅ Downloaded: {blob.name}")

    # 3. Download Audio Asset from audio/ folder
    audio_filename = f"audio/audio_{VIDEO_ID}.mp3"
    audio_path = "voiceover.mp3"
    try:
        raw_bucket.blob(audio_filename).download_to_filename(audio_path)
        print(f"✅ Downloaded audio: {audio_filename}")
    except Exception as e:
        print(f"❌ ERROR: Audio file {audio_filename} not found: {e}")
        return

    # 4. Process with MoviePy
    print("🎬 Merging assets and adding captions...")
    clips = [VideoFileClip(p) for p in video_paths]
    final_video = concatenate_videoclips(clips, method="compose")
    
    audio = AudioFileClip(audio_path)
    final_video = final_video.set_audio(audio)

    # 5. Add Captions (Gold text, centered)
    txt_clip = TextClip(
        bible_quote, 
        fontsize=50, 
        color='gold', 
        font='Arial-Bold', 
        method='caption', 
        size=(final_video.w * 0.8, None)
    )
    txt_clip = txt_clip.set_duration(final_video.duration).set_position('center')
    
    final_result = CompositeVideoClip([final_video, txt_clip])

    # 6. Export and Upload to Processing Bucket
    output_filename = f"final_bible_video_{VIDEO_ID}.mp4"
    final_result.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac")
    
    dest_blob = output_bucket.blob(f"completed_videos/{output_filename}")
    dest_blob.upload_from_filename(output_filename)
    
    print(f"✅ SUCCESS: Video uploaded to {OUTPUT_BUCKET_NAME}/completed_videos/{output_filename}")

if __name__ == "__main__":
    assemble_video()
