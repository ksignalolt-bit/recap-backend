from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import asyncio
import os
from moviepy import VideoFileClip, AudioFileClip

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Auto Recap Backend is Running"}

@app.post("/process-video")
async def process_video(
    video: UploadFile = File(...),
    voice_name: str = Form("my-MM-ThihaNeural")
):
    input_video_path = f"temp_{video.filename}"
    audio_path = "output_voice.mp3"
    output_video_path = f"merged_{video.filename}"

    # Save uploaded video
    with open(input_video_path, "wb") as f:
        f.write(await video.read())

    # Generate Burmese Voice
    burmese_script = "မင်္ဂလာပါခင်ဗျာ။ ဒါကတော့ AI ကနေ အလိုအလျောက် မြန်မာဘာသာနဲ့ ရှင်းပြပေးထားတဲ့ Video Recap ဖြစ်ပါတယ်။"
    tts = edge_tts.Communicate(burmese_script, voice_name)
    await tts.save(audio_path)

    # Merge Video and Audio
    video_clip = VideoFileClip(input_video_path)
    audio_clip = AudioFileClip(audio_path)

    final_clip = video_clip.with_audio(audio_clip) if hasattr(video_clip, 'with_audio') else video_clip.set_audio(audio_clip)
    final_clip.write_videofile(
        output_video_path, 
        codec="libx264", 
        audio_codec="aac"
    )

    video_clip.close()
    audio_clip.close()

    return FileResponse(
        path=output_video_path, 
        filename=f"burmese_recap_{video.filename}", 
        media_type="video/mp4"
    )
