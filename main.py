from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import asyncio
import os
import shutil
import subprocess
import requests
import base64
import glob

# သင့် Google AI Studio API Key
GEMINI_KEY = "AQ.Ab8RN6KorPJHyJVtjQdBkvP-1NzLtkOtTseBdZfuKPw-pAHbMQ"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Movie Recap (Burmese)</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #0f172a; color: #f8fafc; display: flex; justify-content: center; padding: 20px 10px; min-height: 100vh; }
        .container { width: 100%; max-width: 480px; background: #1e293b; border-radius: 20px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155; }
        .header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
        .icon { font-size: 28px; background: #2563eb; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 12px; }
        h1 { font-size: 18px; font-weight: 700; color: #fff; }
        p.sub { font-size: 12px; color: #94a3b8; }
        .upload-card { border: 2px dashed #475569; border-radius: 16px; padding: 26px 15px; text-align: center; background: #0f172a; cursor: pointer; margin-bottom: 16px; }
        input[type="file"] { display: none; }
        label { font-size: 12px; color: #94a3b8; margin-bottom: 6px; display: block; }
        .voice-select { width: 100%; padding: 12px; border-radius: 10px; background: #0f172a; color: #fff; border: 1px solid #475569; margin-bottom: 16px; font-size: 14px; }
        .btn { width: 100%; padding: 16px; background: #2563eb; color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .btn:disabled { background: #475569; cursor: not-allowed; }
        #status { margin-top: 15px; font-size: 13px; text-align: center; color: #38bdf8; line-height: 1.5; }
        #script-preview { margin-top: 15px; padding: 12px; background: #0f172a; border-radius: 10px; font-size: 12px; color: #cbd5e1; display: none; border-left: 4px solid #38bdf8; max-height: 130px; overflow-y: auto; text-align: left; }
        #result-area { margin-top: 20px; display: none; text-align: center; }
        video { width: 100%; border-radius: 12px; margin-top: 10px; max-height: 280px; background: #000; }
        .btn-down { background: #10b981; margin-top: 12px; text-decoration: none; display: inline-block; padding: 14px; border-radius: 10px; color: #fff; font-weight: bold; width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">🎬</div>
            <div>
                <h1>AI Video Story Recap</h1>
                <p class="sub">Full Duration AI Storytelling & Narration</p>
            </div>
        </div>

        <div class="upload-card" onclick="document.getElementById('videoFile').click()">
            <div style="font-size: 32px; margin-bottom: 8px;">📤</div>
            <strong id="file-label" style="font-size: 14px; color: #cbd5e1;">SELECT VIDEO FILE</strong>
            <p style="font-size: 11px; color: #64748b; margin-top: 4px;">Works with any video format</p>
        </div>
        <input type="file" id="videoFile" accept="video/*" onchange="fileSelected(this)">

        <label>Burmese Voice:</label>
        <select id="voice" class="voice-select">
            <option value="my-MM-ThihaNeural">Thiha (Male Voice)</option>
            <option value="my-MM-NilarNeural">Nilar (Female Voice)</option>
        </select>

        <button id="submitBtn" class="btn" onclick="processVideo()">🚀 AI ANALYZE & RECAP</button>

        <div id="status"></div>
        <div id="script-preview"></div>

        <div id="result-area">
            <h3 style="font-size: 14px; color: #4ade80;">✅ Full Recap Video Ready!</h3>
            <video id="previewPlayer" controls playsinline></video>
            <a id="downBtn" class="btn-down" download="ai_story_recap.mp4">📥 DOWNLOAD RECAP VIDEO</a>
        </div>
    </div>

    <script>
        let selectedFile = null;

        function fileSelected(input) {
            if (input.files && input.files[0]) {
                selectedFile = input.files[0];
                document.getElementById('file-label').innerText = "Selected: " + selectedFile.name;
            }
        }

        async function processVideo() {
            if (!selectedFile) {
                alert("Please select a video file first!");
                return;
            }

            const btn = document.getElementById('submitBtn');
            const status = document.getElementById('status');
            const scriptPreview = document.getElementById('script-preview');
            const resultArea = document.getElementById('result-area');
            
            btn.disabled = true;
            btn.innerText = "⏳ AI Analyzing Video...";
            status.innerText = "AI is watching the video scene by scene and writing a Burmese story script...";
            resultArea.style.display = "none";
            scriptPreview.style.display = "none";

            const formData = new FormData();
            formData.append("video", selectedFile);
            formData.append("voice_name", document.getElementById('voice').value);

            try {
                const response = await fetch("/process-video", {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) {
                    const err = await response.text();
                    throw new Error(err || ("Status: " + response.status));
                }

                status.innerText = "Recap video generated successfully!";
                const blob = await response.blob();
                const videoUrl = URL.createObjectURL(blob);
                
                document.getElementById('previewPlayer').src = videoUrl;
                document.getElementById('downBtn').href = videoUrl;
                resultArea.style.display = "block";
            } catch (err) {
                alert(err.message);
                status.innerText = "Error: " + err.message;
            } finally {
                btn.disabled = false;
                btn.innerText = "🚀 AI ANALYZE & RECAP";
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return HTMLResponse(content=HTML_CONTENT)

@app.post("/process-video")
async def process_video(
    video: UploadFile = File(...),
    voice_name: str = Form("my-MM-ThihaNeural")
):
    temp_dir = "/tmp/recap_work"
    os.makedirs(temp_dir, exist_ok=True)

    safe_name = "".join(c for c in video.filename if c.isalnum() or c in "._-")
    input_video_path = os.path.join(temp_dir, f"in_{safe_name}")
    audio_path = os.path.join(temp_dir, "voice.mp3")
    output_video_path = os.path.join(temp_dir, f"out_{safe_name}")

    try:
        # ၁။ Video ဖိုင် သိမ်းဆည်းခြင်း
        with open(input_video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # ၂။ Video မှ Frame ပုံများ ထုတ်ယူခြင်း (ပေါ့ပါးမြန်ဆန်စေရန်)
        frame_pattern = os.path.join(temp_dir, "frame_%d.jpg")
        cmd_extract = [
            "ffmpeg", "-y", "-i", input_video_path,
            "-vf", "fps=1/4,scale=640:-1", "-vframes", "4",
            frame_pattern
        ]
        subprocess.run(cmd_extract, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        image_parts = []
        for img_path in sorted(glob.glob(os.path.join(temp_dir, "frame_*.jpg"))):
            with open(img_path, "rb") as img_file:
                b64_data = base64.b64encode(img_file.read()).decode("utf-8")
                image_parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64_data
                    }
                })

        # ၃။ Gemini AI သို့ Native Query Param ဖြင့် ပို့ပြီး မြန်မာ Recap ဇာတ်ကြောင်း တောင်းဆိုခြင်း
        prompt_text = (
            "ဒီဗီဒီယို ပုံရိပ်တွေကို သေချာကြည့်ပြီး TikTok/Facebook Movie Recap စတိုင်လ်အတိုင်း "
            "ဇာတ်ကောင်တွေရဲ့ လှုပ်ရှားမှု၊ ဖြစ်ပျက်နေတဲ့ အခြေအနေတွေကို "
            "မြန်မာဘာသာစကားဖြင့် စိတ်ဝင်စားဖွယ် ဇာတ်လမ်းတစ်ပုဒ်လို အစအဆုံး အသေးစိတ် ပြန်ပြောပြပေးပါ။ "
            "စာလုံးရေ အနည်းဆုံး စကားလုံး ၁၀၀ မှ ၁၅၀ ခန့် ရှည်လျားသော မြန်မာစာသားသက်သက်သာ ရေးပေးပါ။ အင်္ဂလိပ်စာလုံးလုံး မပါစေရ။"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt_text}] + image_parts}]}

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            burmese_script = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            raise Exception(f"AI Error: {resp.text}")

        # ၄။ ရလာသော ဇာတ်ကြောင်းကို မြန်မာအသံ ထုတ်ယူခြင်း
        communicate = edge_tts.Communicate(burmese_script, voice_name)
        await communicate.save(audio_path)

        # ၅။ မူရင်းဗီဒီယိုအရှည် အပြည့်အဝဖြင့် ပေါင်းစပ်ခြင်း
        cmd_merge = [
            "ffmpeg", "-y",
            "-i", input_video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            output_video_path
        ]
        subprocess.run(cmd_merge, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return FileResponse(
            path=output_video_path,
            filename=f"movie_recap_{safe_name}",
            media_type="video/mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
