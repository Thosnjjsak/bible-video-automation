import os
import requests
import base64
from google.cloud import storage
from moviepy import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, AudioFileClip
def main():
    # 1. Read Inputs from n8n Environment Variables
    video_id = os.environ.get('VIDEO_ID', '1').strip('"')
    bible_quote = os.environ.get('BIBLE_QUOTE', '').strip('"')
    voiceover_url = os.environ.get('VOICEOVER_URL', '').strip('"')
    
    # Process the 3 Pexels URLs
    video_urls_raw = os.environ.get('VIDEO_URLS', '')
    video_urls = [url.strip() for url in video_urls_raw.split(',') if url.strip()]

    print(f"Processing Video ID: {video_id}")

    # 2. Download Voiceover from GCP Bucket link
    print("Downloading voiceover...")
    audio_path = "/tmp/voiceover.mp3"
    with requests.get(voiceover_url) as r:
        r.raise_for_status()
        with open(audio_path, 'wb') as f:
            f.write(r.content)
    audio_clip = AudioFileClip(audio_path)
    # The video duration will match the audio duration
    total_duration = audio_clip.duration 

    # 3. Download and Process the 3 Pexels Scenes
    clips = []
    # Divide total duration by 3 to get length per clip
    clip_duration = total_duration / 3 

    for i, url in enumerate(video_urls[:3]):
        temp_path = f"/tmp/scene_{i}.mp4"
        print(f"Downloading scene {i+1}...")
        with requests.get(url, stream=True) as r:
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
        
        # Resize to 1080p Vertical and trim to fit
        clip = VideoFileClip(temp_path).resized(height=1920).cropped(x_center=540, width=1080)
        clip = clip.subclip(0, clip_duration)
        clips.append(clip)

    # 4. Assemble Video
    background = concatenate_videoclips(clips, method="compose")

    # 5. Create Neo-Mint Captions (#9CAF88)
    txt_clip = TextClip(
        bible_quote,
        fontsize=70,
        color='#9CAF88', 
        stroke_color='black',
        stroke_width=2,
        method='caption',
        size=(900, None), # Center aligned with padding
        font='Arial-Bold'
    ).set_duration(total_duration).set_position('center')

    # 6. Final Composite (Video + Text + Audio)
    final_video = CompositeVideoClip([background, txt_clip]).set_audio(audio_clip)

    # 7. Save Locally
    output_filename = f"final_bible_video_{video_id}.mp4"
    local_output = f"/tmp/{output_filename}"
    final_video.write_videofile(local_output, fps=30, codec="libx264", audio_codec="aac")

    # 8. Upload Final Video back to your Bucket
    client = storage.Client()
    # REPLACE with your actual bucket name
    bucket = client.bucket("project-final-renders") 
    blob = bucket.blob(output_filename)
    blob.upload_from_filename(local_output)
    
    print(f"Success! Video uploaded: {output_filename}")

if __name__ == "__main__":
    main()