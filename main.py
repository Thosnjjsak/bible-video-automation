import os
import requests
import math
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from google.cloud import storage

def main():
    # 1. Variables
    video_urls = os.environ.get('VIDEO_URLS', '').split(',')
    # Triple-check backup for the script text
    voiceover_script = os.environ.get('VOICEOVER_SCRIPT') or os.environ.get('BIBLE_QUOTE') or "Strength in the Peaks"
    voiceover_url = os.environ.get('VOICEOVER_URL')
    video_id = os.environ.get('VIDEO_ID', '1')
    dest_bucket_name = "project-final-renders"

    # 2. Audio Setup
    r_audio = requests.get(voiceover_url)
    with open("audio.mp3", "wb") as f: f.write(r_audio.content)
    audio_clip = AudioFileClip("audio.mp3")
    total_duration = audio_clip.duration

    # 3. Background Assembly
    num_videos = len(video_urls)
    duration_per_clip = total_duration / num_videos
    final_clips = []

    for i, url in enumerate(video_urls):
        temp_v = f"temp_{i}.mp4"
        v_res = requests.get(url)
        with open(temp_v, "wb") as f: f.write(v_res.content)
        
        # Standardize to vertical 9:16
        clip = VideoFileClip(temp_v).resized(height=1920).cropped(x_center=540, width=1080)
        
        if clip.duration < duration_per_clip:
            loop_count = math.ceil(duration_per_clip / clip.duration)
            clip = concatenate_videoclips([clip] * loop_count)
        
        # Trim to exact fit
        clip = clip.subclipped(0, duration_per_clip)
        final_clips.append(clip)

    # Use 'compose' method for smoother transitions between different resolutions/bitrates
    background = concatenate_videoclips(final_clips, method="compose")

    # 4. Text Styling (Bottom-Middle Position)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_selection = font_path if os.path.exists(font_path) else 'sans-serif'

    txt_clip = TextClip(
        text=voiceover_script,
        font=font_selection, 
        font_size=50, 
        color='yellow',
        method='caption', 
        size=(850, None), 
        text_align='center'
    ).with_duration(total_duration).with_position(('center', 1450))

    # 5. Export
    final_video = CompositeVideoClip([background, txt_clip]).with_audio(audio_clip)
    output_name = f"final_video_{video_id}.mp4"
    final_video.write_videofile(output_name, fps=24, codec="libx264", audio_codec="aac")

    # 6. Upload to GCP
    storage_client = storage.Client()
    bucket = storage_client.bucket(dest_bucket_name)
    blob = bucket.blob(output_name)
    blob.upload_from_filename(output_name)
    print(f"Successfully uploaded {output_name}")

if __name__ == "__main__":
    main()