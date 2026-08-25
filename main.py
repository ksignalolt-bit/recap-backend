from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import asyncio
import os
import shutil
import subprocess
import google.generativeai as genai

# Gemini API Key Configuration
genai.configure(api_key="AQ.Ab8RN6Jv-N9P1UxpIzLnNTGO51kK_qaXjo-vC2E5FFkWTw7Euw")

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
    <title>AI Video Story Recap (Burmese)</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #0f172a; color: #f8fafc; display: flex; justify-content: center; padding: 20px 10px; min-height: 100vh; }
        .container { width: 100%; max-width: 480px; background: #1e293b; border-radius: 20px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155; }
        .header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
        .icon { font-size: 28px; background: #2563eb; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; border-radius: 12px; }
        h1 { font-size: 18px; font-weight: 700; color: #fff; }
        p.sub { font-size: 12px; color: #94a3b8; }
        .upload-card { border: 2px dashed #475569; border-radius: 16px; padding: 30px 15px; text-align: center; background: #0f172a; cursor: pointer; margin-bottom: 20px; }
        input[type="file"] { display: none; }
        .voice-select { width: 100%; padding: 12px; border-radius: 10px; background: #0f172a; color: #fff; border: 1px solid #475569; margin-bottom: 20px; font-size: 14px; }
        .btn { width: 100%; padding: 16px; background: #2563eb; color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .btn:disabled { background: #475569; cursor: not-allowed; }
        #status { margin-top: 15px; font-size: 13px; text-align: center; color: #38bdf8; line-height: 1.5; }
        #result-area { margin-top: 20px; display: none; text-align: center; }
        video { width: 100%; border-radius: 12px; margin-top: 10px; max-height: 260px; background: #000; }
        .btn-down { background: #10b981; margin-top: 12px; text-decoration: none; display: inline-block; padding: 14px; border-radius: 10px; color: #fff; font-weight: bold; width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">🎬</div>
            <div>
                <h1>AI Video Story Recap</h1>
                <p class="sub">AI Content Analysis & Burmese Narration</p>
            </div>
        </div>

        <div class="upload-card" onclick="document.getElementById('videoFile').click()">
            <div style="font-size: 32px; margin-bottom: 8px;">📤</div>
            <strong id="file-label" style="font-size: 14px; color: #cbd5e1;">SELECT VIDEO TO ANALYZE</strong>
            <p style="font-size: 11px; color: #64748b; margin-top: 4px;">Click to browse from phone</p>
        </div>
        <input type="file" id="videoFile" accept="video/*" onchange="fileSelected(this)">

        <label style="font-size: 12px; color: #94a3b8; margin-bottom: 6px; display: block;">Burmese Voice Style:</label>
        <select id="voice" class="voice-select">
            <option value="my-MM-ThihaNeural">Thiha (Narrator Male)</option>
            <option value="my-MM-NilarNeural">Nilar (Narrator Female)</option>
        </select>

        <button id="submitBtn" class="btn" onclick="processVideo()">🚀 AI ANALYZE & RECAP</button>

        <div id="status"></div>

        <div id="result-area">
            <h3 style="font-size: 14px; color: #4ade80;">✅ Full Recap Video Ready!</h3>
            <video id="previewPlayer" controls playsinline></video>
            <a id="downBtn" class="btn-down" download="ai_recap.mp4">📥 DOWNLOAD RECAP VIDEO</a>
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
            const resultArea = document.getElementById('result-area');
            
            btn.disabled = true;
            btn.innerText = "⏳ AI is Watching & Analyzing...";
            status.innerText = "AI is watching your video frames and writing a Burmese story script...";
            resultArea.style.display = "none";

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

                status.innerText = "Merging audio into video complete!";
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

        # ၂။ Gemini AI သို့ Video တင်ပြီး မြန်မာလို Recap ရေးခိုင်းခြင်း
        video_ai_file = genai.upload_file(path=input_video_path)
        
        while video_ai_file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            video_ai_file = genai.get_file(video_ai_file.name)

        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "ဒီဗီဒီယိုထဲမှာ ဘာတွေဖြစ်ပျက်နေလဲဆိုတာ သေချာကြည့်ပြီး "
            "Facebook/TikTok Movie Recap ပုံစံမျိုး စိတ်ဝင်စားဖွယ် မြန်မာဘာသာစကားဖြင့် "
            "အနှစ်ချုပ် ဇာတ်ကြောင်းပြန်ပြောပေးပါ။ စာသားသက်သက်သာ ရေးပေးပါ (အင်္ဂလိပ်စာနှင့် emoji များ မပါစေရ)။"
        )
        response = model.generate_content([video_ai_file, prompt])
        burmese_script = response.text.strip()

        # ၃။ AI ဇာတ်ကြောင်းကို Edge-TTS ဖြင့် အသံဖိုင်ထုတ်ခြင်း
        communicate = edge_tts.Communicate(burmese_script, voice_name)
        await communicate.save(audio_path)

        # ၄။ ဗီဒီယိုနှင့် မြန်မာအသံ ပေါင်းစပ်ခြင်း
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_video_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return FileResponse(
            path=output_video_path,
            filename=f"ai_recap_{safe_name}",
            media_type="video/mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
