import os
import requests
import math
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from google.cloud import storage

def main():
    # 1. Variables
    video_urls = os.environ.get('VIDEO_URLS', '').split(',')
    voiceover_script = os.environ.get('VOICEOVER_SCRIPT') or os.environ.get('BIBLE_QUOTE', 'Strength for the Journey')
    voiceover_url = os.environ.get('VOICEOVER_URL')
    video_id = os.environ.get('VIDEO_ID', '1')
    dest_bucket_name = "project-final-renders" # Ensure this is defined for the upload

    # 2. Audio Setup
    r_audio = requests.get(voiceover_url)
    with open("audio.mp3", "wb") as f: f.write(r_audio.content)
    audio_clip = AudioFileClip("audio.mp3")
    total_duration = audio_clip.duration

    # 3. Smoother Background Assembly
    num_videos = len(video_urls)
    # We add 1 second to each clip's duration to account for the overlap in cross-fading
    duration_per_clip = (total_duration / num_videos) + 1 
    final_clips = []

    for i, url in enumerate(video_urls):
        temp_v = f"temp_{i}.mp4"
        v_res = requests.get(url)
        with open(temp_v, "wb") as f: f.write(v_res.content)
        
        # Vertical 9:16 crop using MoviePy 2.0 syntax
        clip = VideoFileClip(temp_v).resized(height=1920).cropped(x_center=540, width=1080)
        
        if clip.duration < duration_per_clip:
            loop_count = math.ceil(duration_per_clip / clip.duration)
            clip = concatenate_videoclips([clip] * loop_count)
        
        # Trim and add a 1-second crossfade transition
        clip = clip.subclipped(0, duration_per_clip).crossfadein(1.0)
        final_clips.append(clip)

    # Padding the concatenation for a smoother flow
    background = concatenate_videoclips(final_clips, method="compose", padding=-1)

    # 4. Text Styling (Refined for a cleaner look)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_selection = font_path if os.path.exists(font_path) else 'sans-serif'

    txt_clip = TextClip(
        text=voiceover_script,
        font=font_selection, 
        font_size=40, # Reduced slightly from 45 to prevent 'buggy' or cramped text
        color='yellow',
        method='caption', 
        size=(850, None), # Increased width to 850 for better paragraph flow
        text_align='center'
    ).with_duration(total_duration).with_position(('center', 1450)) # Lower third positioning

    # 5. Export
    final_video = CompositeVideoClip([background, txt_clip]).with_audio(audio_clip)
    output_name = f"final_video_{video_id}.mp4"
    final_video.write_videofile(output_name, fps=24, codec="libx264", audio_codec="aac")

    # 6. UPLOAD TO GCP BUCKET
    print(f"Uploading {output_name} to {dest_bucket_name}...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(dest_bucket_name)
    blob = bucket.blob(output_name)
    blob.upload_from_filename(output_name)
    print("Upload successful!")

if __name__ == "__main__":
    main()import os
import requests
import math
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from google.cloud import storage

def main():
    # 1. Variables
    video_urls = os.environ.get('VIDEO_URLS', '').split(',')
    voiceover_script = os.environ.get('VOICEOVER_SCRIPT') or os.environ.get('BIBLE_QUOTE', 'Strength for the Journey')
    voiceover_url = os.environ.get('VOICEOVER_URL')
    video_id = os.environ.get('VIDEO_ID', '1')
    dest_bucket_name = "project-final-renders" # Ensure this is defined for the upload

    # 2. Audio Setup
    r_audio = requests.get(voiceover_url)
    with open("audio.mp3", "wb") as f: f.write(r_audio.content)
    audio_clip = AudioFileClip("audio.mp3")
    total_duration = audio_clip.duration

    # 3. Smoother Background Assembly
    num_videos = len(video_urls)
    # We add 1 second to each clip's duration to account for the overlap in cross-fading
    duration_per_clip = (total_duration / num_videos) + 1 
    final_clips = []

    for i, url in enumerate(video_urls):
        temp_v = f"temp_{i}.mp4"
        v_res = requests.get(url)
        with open(temp_v, "wb") as f: f.write(v_res.content)
        
        # Vertical 9:16 crop using MoviePy 2.0 syntax
        clip = VideoFileClip(temp_v).resized(height=1920).cropped(x_center=540, width=1080)
        
        if clip.duration < duration_per_clip:
            loop_count = math.ceil(duration_per_clip / clip.duration)
            clip = concatenate_videoclips([clip] * loop_count)
        
        # Trim and add a 1-second crossfade transition
        clip = clip.subclipped(0, duration_per_clip).crossfadein(1.0)
        final_clips.append(clip)

    # Padding the concatenation for a smoother flow
    background = concatenate_videoclips(final_clips, method="compose", padding=-1)

    # 4. Text Styling (Refined for a cleaner look)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_selection = font_path if os.path.exists(font_path) else 'sans-serif'

    txt_clip = TextClip(
        text=voiceover_script,
        font=font_selection, 
        font_size=40, # Reduced slightly from 45 to prevent 'buggy' or cramped text
        color='yellow',
        method='caption', 
        size=(850, None), # Increased width to 850 for better paragraph flow
        text_align='center'
    ).with_duration(total_duration).with_position(('center', 1450)) # Lower third positioning

    # 5. Export
    final_video = CompositeVideoClip([background, txt_clip]).with_audio(audio_clip)
    output_name = f"final_video_{video_id}.mp4"
    final_video.write_videofile(output_name, fps=24, codec="libx264", audio_codec="aac")

    # 6. UPLOAD TO GCP BUCKET
    print(f"Uploading {output_name} to {dest_bucket_name}...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(dest_bucket_name)
    blob = bucket.blob(output_name)
    blob.upload_from_filename(output_name)
    print("Upload successful!")

if __name__ == "__main__":
    main()