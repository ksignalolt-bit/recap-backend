from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from PIL import Image
import edge_tts
import asyncio
import os
import shutil
import subprocess
import glob

# Gemini AI Studio Key
GEMINI_KEY = "AQ.Ab8RN6KgTVyaSRbAPIvnBHglR5vhTytORJTiL81XDB-sI5pKSA"
genai.configure(api_key=GEMINI_KEY)

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
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: sans-serif; }
        body { background: #0f172a; color: #f8fafc; display: flex; justify-content: center; padding: 20px 10px; }
        .container { width: 100%; max-width: 480px; background: #1e293b; border-radius: 16px; padding: 20px; }
        .upload-card { border: 2px dashed #475569; border-radius: 12px; padding: 24px; text-align: center; cursor: pointer; margin-bottom: 16px; }
        input[type="file"] { display: none; }
        .btn { width: 100%; padding: 14px; background: #2563eb; color: #fff; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; }
        .btn:disabled { background: #475569; }
        #status { margin-top: 15px; font-size: 13px; text-align: center; color: #38bdf8; }
        #result-area { margin-top: 20px; display: none; text-align: center; }
        video { width: 100%; border-radius: 10px; margin-top: 10px; background: #000; }
        .btn-down { background: #10b981; margin-top: 10px; display: block; padding: 12px; border-radius: 8px; color: #fff; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="margin-bottom: 15px;">🎬 AI Video Recap (Burmese)</h2>
        <div class="upload-card" onclick="document.getElementById('videoFile').click()">
            <strong id="file-label">SELECT VIDEO FILE</strong>
        </div>
        <input type="file" id="videoFile" accept="video/*" onchange="fileSelected(this)">

        <button id="submitBtn" class="btn" onclick="processVideo()">🚀 AI ANALYZE & RECAP</button>
        <div id="status"></div>

        <div id="result-area">
            <h3>✅ Recap Video Ready!</h3>
            <video id="previewPlayer" controls playsinline></video>
            <a id="downBtn" class="btn-down" download="recap_video.mp4">📥 DOWNLOAD</a>
        </div>
    </div>

    <script>
        let selectedFile = null;
        function fileSelected(input) {
            if (input.files && input.files[0]) {
                selectedFile = input.files[0];
                document.getElementById('file-label').innerText = selectedFile.name;
            }
        }
        async function processVideo() {
            if (!selectedFile) return alert("Select video first!");
            const btn = document.getElementById('submitBtn');
            const status = document.getElementById('status');
            const resultArea = document.getElementById('result-area');
            
            btn.disabled = true;
            btn.innerText = "⏳ Gemini 1.5 Flash Analyzing...";
            status.innerText = "Gemini is analyzing video frames and writing Burmese recap...";
            resultArea.style.display = "none";

            const formData = new FormData();
            formData.append("video", selectedFile);

            try {
                const response = await fetch("/process-video", { method: "POST", body: formData });
                if (!response.ok) throw new Error(await response.text());
                
                const blob = await response.blob();
                const videoUrl = URL.createObjectURL(blob);
                document.getElementById('previewPlayer').src = videoUrl;
                document.getElementById('downBtn').href = videoUrl;
                resultArea.style.display = "block";
                status.innerText = "Completed!";
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
async def process_video(video: UploadFile = File(...)):
    temp_dir = "/tmp/recap_work"
    os.makedirs(temp_dir, exist_ok=True)

    safe_name = "".join(c for c in video.filename if c.isalnum() or c in "._-")
    input_video_path = os.path.join(temp_dir, f"in_{safe_name}")
    audio_path = os.path.join(temp_dir, "voice.mp3")
    output_video_path = os.path.join(temp_dir, f"out_{safe_name}")

    try:
        # ၁။ Save Video
        with open(input_video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # ၂။ Extract Frame Images
        frame_pattern = os.path.join(temp_dir, "frame_%d.jpg")
        cmd_extract = [
            "ffmpeg", "-y", "-i", input_video_path,
            "-vf", "fps=1/3,scale=640:-1", "-vframes", "4",
            frame_pattern
        ]
        subprocess.run(cmd_extract, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        image_files = sorted(glob.glob(os.path.join(temp_dir, "frame_*.jpg")))
        if not image_files:
            raise Exception("Cannot extract frames from video")

        pil_images = [Image.open(f) for f in image_files]

        # ၃။ Gemini 1.5 Flash Vision Call via Official SDK
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "ဒီဗီဒီယိုကနေ ရိုက်ကူးထားတဲ့ ပုံရိပ်တွေကို သေချာကြည့်ပါ။ "
            "ဗီဒီယိုထဲမှာပါတဲ့ လူတွေ၊ သူတို့ဘာလုပ်နေလဲ၊ အခြေအနေနဲ့ အဖြစ်အပျက်တွေကို အတိအကျ သုံးသပ်ပြီး "
            "Facebook Movie Recap ပုံစံမျိုး မြန်မာစကားပြေဖြင့် စိတ်ဝင်စားဖွယ် ဇာတ်ကြောင်းပြန်ပြောပြပါ။ "
            "အင်္ဂလိပ်စာလုံးဝ မပါစေရ။ မြန်မာစာသက်သက်သာ ရေးပေးပါ။"
        )

        response = model.generate_content([prompt] + pil_images)
        burmese_script = response.text.strip()

        if not burmese_script:
            raise Exception("Gemini returned empty script")

        # ၄။ Edge-TTS Burmese Audio
        communicate = edge_tts.Communicate(burmese_script, "my-MM-ThihaNeural")
        await communicate.save(audio_path)

        # ၅။ Merge Video and Audio
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
            filename=f"recap_{safe_name}",
            media_type="video/mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
