import os
import requests
import math
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

def main():
    # 1. Environment Variables
    # Ensure these match the keys you set in your n8n HTTP Request node
    video_urls = os.environ.get('VIDEO_URLS', '').split(',')
    voiceover_script = os.environ.get('VOICEOVER_SCRIPT', 'No script provided')
    voiceover_url = os.environ.get('VOICEOVER_URL')
    video_id = os.environ.get('VIDEO_ID', '1')

    # 2. Audio Setup
    # Download the voiceover from the URL provided by n8n
    r_audio = requests.get(voiceover_url)
    with open("audio.mp3", "wb") as f:
        f.write(r_audio.content)
    
    audio_clip = AudioFileClip("audio.mp3")
    total_duration = audio_clip.duration

    # 3. Balanced Background Assembly
    # Distributes available videos evenly across the audio duration
    num_videos = len(video_urls)
    duration_per_clip = total_duration / num_videos
    final_clips = []

    for i, url in enumerate(video_urls):
        temp_video_path = f"temp_{i}.mp4"
        v_res = requests.get(url)
        with open(temp_video_path, "wb") as f:
            f.write(v_res.content)
        
        # MoviePy 2.0 Syntax: .resized() and .cropped() for 9:16 vertical
        clip = VideoFileClip(temp_video_path).resized(height=1920).cropped(x_center=540, width=1080)
        
        # If the Pexels clip is shorter than its 10s slot, we loop it
        if clip.duration < duration_per_clip:
            loop_count = math.ceil(duration_per_clip / clip.duration)
            clip = concatenate_videoclips([clip] * loop_count)
        
        # Trim the clip to fit exactly into its allocated time slot
        clip = clip.subclipped(0, duration_per_clip)
        final_clips.append(clip)

    background = concatenate_videoclips(final_clips)

    # 4. "Philosophaire" Style Text Effect
    # Font Fallback: Direct path is best for Google Cloud Run (Linux)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_selection = font_path if os.path.exists(font_path) else 'sans-serif'

    # Create a drop shadow for better readability
    shadow_clip = TextClip(
        text=voiceover_script,
        font=font_selection,
        font_size=72,
        color='black',
        method='caption',
        size=(910, None),
        text_align='center'
    ).with_duration(total_duration).with_position(('center', 965)).with_opacity(0.6)

    # Main highlight text (Yellow)
    txt_clip = TextClip(
        text=voiceover_script,
        font=font_selection,
        font_size=70,
        color='yellow',
        method='caption',
        size=(900, None),
        text_align='center'
    ).with_duration(total_duration).with_position(('center', 960))

    # 5. Final Composition and Export
    final_video = CompositeVideoClip([background, shadow_clip, txt_clip]).with_audio(audio_clip)
    
    output_path = f"final_video_{video_id}.mp4"
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    main()