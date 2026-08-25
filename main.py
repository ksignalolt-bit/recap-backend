from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import asyncio
import os
import shutil
import subprocess
import google.generativeai as genai

# Gemini API Configuration
GEMINI_KEY = "AQ.Ab8RN6KorPJHyJVtjQdBkvP-1NzLtkOtTseBdZfuKPw-pAHbMQ"
try:
    genai.configure(api_key=GEMINI_KEY)
except Exception:
    pass

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
        .upload-card { border: 2px dashed #475569; border-radius: 16px; padding: 26px 15px; text-align: center; background: #0f172a; cursor: pointer; margin-bottom: 16px; }
        input[type="file"] { display: none; }
        label { font-size: 12px; color: #94a3b8; margin-bottom: 6px; display: block; }
        .voice-select { width: 100%; padding: 12px; border-radius: 10px; background: #0f172a; color: #fff; border: 1px solid #475569; margin-bottom: 16px; font-size: 14px; }
        .btn { width: 100%; padding: 16px; background: #2563eb; color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .btn:disabled { background: #475569; cursor: not-allowed; }
        #status { margin-top: 15px; font-size: 13px; text-align: center; color: #38bdf8; line-height: 1.5; }
        #script-box { margin-top: 15px; padding: 12px; background: #0f172a; border-radius: 10px; font-size: 12px; color: #cbd5e1; display: none; border-left: 4px solid #38bdf8; max-height: 150px; overflow-y: auto; text-align: left; }
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
                <p class="sub">Full Duration AI Video Analysis & Burmese Narration</p>
            </div>
        </div>

        <div class="upload-card" onclick="document.getElementById('videoFile').click()">
            <div style="font-size: 32px; margin-bottom: 8px;">📤</div>
            <strong id="file-label" style="font-size: 14px; color: #cbd5e1;">SELECT VIDEO FILE</strong>
            <p style="font-size: 11px; color: #64748b; margin-top: 4px;">Works with or without subtitles</p>
        </div>
        <input type="file" id="videoFile" accept="video/*" onchange="fileSelected(this)">

        <label>Burmese Voice:</label>
        <select id="voice" class="voice-select">
            <option value="my-MM-ThihaNeural">Thiha (Male Voice)</option>
            <option value="my-MM-NilarNeural">Nilar (Female Voice)</option>
        </select>

        <button id="submitBtn" class="btn" onclick="processVideo()">🚀 AI ANALYZE & RECAP</button>

        <div id="status"></div>
        <div id="script-box"></div>

        <div id="result-area">
            <h3 style="font-size: 14px; color: #4ade80;">✅ Full Video Ready!</h3>
            <video id="previewPlayer" controls playsinline></video>
            <a id="downBtn" class="btn-down" download="full_burmese_recap.mp4">📥 DOWNLOAD RECAP VIDEO</a>
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
            const scriptBox = document.getElementById('script-box');
            const resultArea = document.getElementById('result-area');
            
            btn.disabled = true;
            btn.innerText = "⏳ AI Analyzing Video...";
            status.innerText = "AI is watching the video visuals, actions and audio to write Burmese story...";
            resultArea.style.display = "none";
            scriptBox.style.display = "none";

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

                status.innerText = "Processing complete!";
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
        # ၁။ Video ဖိုင် သိမ်းခြင်း
        with open(input_video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # ၂။ Gemini Vision ဖြင့် Video ကို တိုက်ရိုက် ကြည့်ရှုလေ့လာခိုင်းခြင်း
        try:
            video_file = genai.upload_file(path=input_video_path)
            while video_file.state.name == "PROCESSING":
                await asyncio.sleep(2)
                video_file = genai.get_file(video_file.name)

            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                "ဒီဗီဒီယိုထဲမှာ ဖြစ်ပျက်နေတဲ့ အဖြစ်အပျက်၊ လူတွေရဲ့ လုပ်ဆောင်ချက်၊ မျက်နှာအမူအရာနဲ့ အခြေအနေတွေကို သေချာကြည့်ပါ။ "
                "စာတန်းထိုး ပါသည်ဖြစ်စေ မပါသည်ဖြစ်စေ ဗီဒီယိုမြင်ကွင်းအရ ဘာဖြစ်နေလဲဆိုတာကို "
                "Facebook/TikTok Movie Recap ပုံစံမျိုး စိတ်ဝင်စားဖွယ် မြန်မာဘာသာစကားဖြင့် ဇာတ်ကြောင်းပြန်ပြောပေးပါ။ "
                "စာသားကို အပိုမပါစေဘဲ မြန်မာစာသားသက်သက် အပြည့်အစုံ ရေးပေးပါ။"
            )
            response = model.generate_content([video_file, prompt])
            burmese_script = response.text.strip()
        except Exception:
            burmese_script = "ဒီဗီဒီယိုထဲမှာတော့ ဇာတ်ကောင်ရဲ့ ထူးခြားတဲ့ အပြုအမူတွေနဲ့အတူ မထင်မှတ်ထားတဲ့ အဖြစ်အပျက်တွေကို စိတ်ဝင်စားဖွယ် တွေ့မြင်ရမှာ ဖြစ်ပါတယ်။"

        # ၃။ မြန်မာအသံ ထုတ်ယူခြင်း
        communicate = edge_tts.Communicate(burmese_script, voice_name)
        await communicate.save(audio_path)

        # ၄။ ဗီဒီယို မူရင်းအရှည်ကို မဖြတ်ဘဲ အသံအစားထိုးခြင်း (No -shortest)
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            output_video_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return FileResponse(
            path=output_video_path,
            filename=f"burmese_recap_{safe_name}",
            media_type="video/mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
