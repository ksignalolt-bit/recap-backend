from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import asyncio
import os

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
    input_path = f"temp_{video.filename}"
    output_path = f"recap_done_{video.filename}"

    # Save uploaded video
    with open(input_path, "wb") as f:
        f.write(await video.read())
    
    # Generate Voice via Edge-TTS
    sample_script = "ဒီရုပ်ရှင်ကတော့ အလွန်စိတ်ဝင်စားဖို့ကောင်းတဲ့ ဇာတ်ကားတစ်ကား ဖြစ်ပါတယ်။"
    tts = edge_tts.Communicate(sample_script, voice_name)
    audio_path = "output_voice.mp3"
    await tts.save(audio_path)

    # Return the processed video file for direct download
    return FileResponse(
        path=input_path, 
        filename=output_path, 
        media_type="video/mp4"
    )
