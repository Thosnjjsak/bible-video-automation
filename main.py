import os
import requests
import math
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
from google.cloud import storage

def main():
    # 1. Variables - Pointing to project-raw-assets
    video_urls = os.environ.get('VIDEO_URLS', '').split(',')
    voiceover_url = os.environ.get('VOICEOVER_URL')
    video_id = os.environ.get('VIDEO_ID', '1')
    dest_bucket_name = "project-raw-assets" 

    # 2. Audio Setup
    r_audio = requests.get(voiceover_url)
    with open("audio.mp3", "wb") as f: f.write(r_audio.content)
    audio_clip = AudioFileClip("audio.mp3")
    total_duration = audio_clip.duration

    # 3. Background Assembly (Merging 3 clips)
    num_videos = len(video_urls)
    duration_per_clip = total_duration / num_videos
    final_clips = []

    for i, url in enumerate(video_urls):
        temp_v = f"temp_{i}.mp4"
        v_res = requests.get(url)
        with open(temp_v, "wb") as f: f.write(v_res.content)
        
        # 9:16 Vertical Standard
        clip = VideoFileClip(temp_v).resized(height=1920).cropped(x_center=540, width=1080)
        
        # Ensure clip isn't too short
        if clip.duration < duration_per_clip:
            loop_count = math.ceil(duration_per_clip / clip.duration)
            clip = concatenate_videoclips([clip] * loop_count)
        
        final_clips.append(clip.subclipped(0, duration_per_clip))

    # 4. Final Composition (Merged without text)
    final_video = concatenate_videoclips(final_clips, method="compose").with_audio(audio_clip)
    output_name = f"raw_merged_{video_id}.mp4"
    final_video.write_videofile(output_name, fps=24, codec="libx264", audio_codec="aac")

    # 5. Upload to GCP
    storage_client = storage.Client()
    bucket = storage_client.bucket(dest_bucket_name)
    blob = bucket.blob(output_name)
    blob.upload_from_filename(output_name)
    print(f"Successfully uploaded {output_name} to project-raw-assets.")

if __name__ == "__main__":
    main()