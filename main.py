from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import edge_tts
import asyncio
import os
import shutil
import subprocess

# Gemini API Key
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
    <title>AI Movie Recap (Dialogue to Burmese)</title>
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
        <h2 style="margin-bottom: 15px;">🎬 AI Dialogue Recap (Burmese)</h2>
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
            btn.innerText = "⏳ Listening & Writing Recap...";
            status.innerText = "Gemini is listening to video audio/dialogue and writing Burmese recap...";
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
    extracted_audio_path = os.path.join(temp_dir, "input_dialogue.mp3")
    burmese_audio_path = os.path.join(temp_dir, "burmese_voice.mp3")
    output_video_path = os.path.join(temp_dir, f"out_{safe_name}")

    try:
        # ၁။ Save Video
        with open(input_video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # ၂။ Extract Original Audio/Dialogue using FFmpeg
        cmd_extract_audio = [
            "ffmpeg", "-y", "-i", input_video_path,
            "-vn", "-acodec", "libmp3lame", "-b:a", "128k",
            extracted_audio_path
        ]
        subprocess.run(cmd_extract_audio, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # ၃။ Gemini Audio Understanding (နားထောင်ပြီး မြန်မာ Recap ရေးခိုင်းခြင်း)
        audio_file_upload = genai.upload_file(path=extracted_audio_path)
        
        prompt = (
            "ဒီ audio ထဲမှာပါတဲ့ ဇာတ်ကောင်တွေ ပြောနေတဲ့ စကားပြောတွေ၊ အသံတွေနဲ့ အကြောင်းအရာကို သေချာနားထောင်ပါ။ "
            "သူတို့ ဘာအကြောင်းပြောနေလဲ၊ ဘာအဓိပ္ပာယ်လဲဆိုတာကို နားလည်အောင် လုပ်ပြီး "
            "စိတ်ဝင်စားစရာကောင်းတဲ့ Facebook/TikTok Movie Recap ဇာတ်ကြောင်းပြော ပုံစံမျိုးဖြင့် "
            "မြန်မာဘာသာစကား သက်သက်ဖြင့် ရှင်းလင်း ပြန်ပြောပြပေးပါ။ "
            "အင်္ဂလိပ်စာ လုံးဝ မပါစေရ။"
        )

        model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
        response = model.generate_content([prompt, audio_file_upload])
        burmese_script = response.text.strip()

        if not burmese_script:
            raise Exception("AI could not generate recap from dialogue")

        # ၄။ Edge-TTS Burmese Narration
        communicate = edge_tts.Communicate(burmese_script, "my-MM-ThihaNeural")
        await communicate.save(burmese_audio_path)

        # ၅။ Merge Video with new Burmese Narration
        cmd_merge = [
            "ffmpeg", "-y",
            "-i", input_video_path,
            "-i", burmese_audio_path,
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
