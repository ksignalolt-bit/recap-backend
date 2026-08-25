from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import asyncio
import os
import shutil
import subprocess
import requests

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
        .input-box { width: 100%; padding: 12px; border-radius: 10px; background: #0f172a; color: #fff; border: 1px solid #475569; margin-bottom: 14px; font-size: 13px; }
        textarea.input-box { resize: vertical; min-height: 60px; }
        .btn { width: 100%; padding: 16px; background: #2563eb; color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .btn:disabled { background: #475569; cursor: not-allowed; }
        #status { margin-top: 15px; font-size: 13px; text-align: center; color: #38bdf8; line-height: 1.5; }
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
                <p class="sub">Burmese Storytelling & Full Video Recapper</p>
            </div>
        </div>

        <div class="upload-card" onclick="document.getElementById('videoFile').click()">
            <div style="font-size: 32px; margin-bottom: 8px;">📤</div>
            <strong id="file-label" style="font-size: 14px; color: #cbd5e1;">SELECT VIDEO FILE</strong>
            <p style="font-size: 11px; color: #64748b; margin-top: 4px;">Upload video (MP4)</p>
        </div>
        <input type="file" id="videoFile" accept="video/*" onchange="fileSelected(this)">

        <label>Video Story/Topic (ရုပ်ရှင်ခေါင်းစဉ် သို့မဟုတ် အကြောင်းအရာ အကြမ်းဖျင်း - Optional):</label>
        <textarea id="storyTopic" class="input-box" placeholder="ဥပမာ- ရုံးခန်းထဲက မိန်းကလေးတစ်ယောက်ရဲ့ ထူးဆန်းတဲ့ အဖြစ်အပျက် (မထည့်လဲ ရပါတယ်)"></textarea>

        <label>Burmese Voice:</label>
        <select id="voice" class="input-box">
            <option value="my-MM-ThihaNeural">Thiha (Narrator Male)</option>
            <option value="my-MM-NilarNeural">Nilar (Narrator Female)</option>
        </select>

        <button id="submitBtn" class="btn" onclick="processVideo()">🚀 AI ANALYZE & RECAP</button>

        <div id="status"></div>

        <div id="result-area">
            <h3 style="font-size: 14px; color: #4ade80;">✅ Full Video Recap Ready!</h3>
            <video id="previewPlayer" controls playsinline></video>
            <a id="downBtn" class="btn-down" download="burmese_movie_recap.mp4">📥 DOWNLOAD RECAP VIDEO</a>
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
            btn.innerText = "⏳ AI Analyzing & Generating...";
            status.innerText = "Writing full Burmese storytelling recap and merging voice...";
            resultArea.style.display = "none";

            const formData = new FormData();
            formData.append("video", selectedFile);
            formData.append("voice_name", document.getElementById('voice').value);
            formData.append("story_topic", document.getElementById('storyTopic').value);

            try {
                const response = await fetch("/process-video", {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) {
                    const err = await response.text();
                    throw new Error(err || ("Status: " + response.status));
                }

                status.innerText = "Recap video created successfully!";
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
    voice_name: str = Form("my-MM-ThihaNeural"),
    story_topic: str = Form("")
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

        # ၂။ AI Story Recap Script Generator (Pollinations Free AI Engine)
        topic_info = f"အကြောင်းအရာ- {story_topic}" if story_topic.strip() else "ဗီဒီယိုဇာတ်လမ်း"
        system_prompt = (
            f"သင်သည် နာမည်ကြီး Movie Recap / Storytelling ဖန်တီးသူတစ်ဦးဖြစ်သည်။ {topic_info} အတွက် "
            "Facebook/TikTok တွင် ကြည့်ရှုသူ စိတ်ဝင်စားစေမည့် မြန်မာဘာသာစကားဖြင့် "
            "အစ၊ အလယ်၊ အဆုံး ပြည့်စုံသော Movie Recap ဇာတ်ကြောင်းကို ရေးပေးပါ။ "
            "စာလုံးရေ အနည်းဆုံး ၁၅၀ စကားလုံးခန့် ရှည်လျားပြီး နားထောင်ရ ကောင်းမွန်သော မြန်မာစာသားသက်သက်သာ ရေးပေးပါ (အင်္ဂလိပ်စာလုံးဝ မပါစေရ)။"
        )

        try:
            ai_url = f"https://text.pollinations.ai/{requests.utils.quote(system_prompt)}"
            res = requests.get(ai_url, timeout=20)
            if res.status_code == 200 and len(res.text.strip()) > 30:
                burmese_script = res.text.strip()
            else:
                burmese_script = (
                    "ဇာတ်လမ်းအစမှာတော့ အဓိကဇာတ်ကောင်ရဲ့ ထူးခြားဆန်းကြယ်တဲ့ လှုပ်ရှားမှုတွေနဲ့အတူ "
                    "မထင်မှတ်ထားတဲ့ အပြောင်းအလဲတွေကို မြင်တွေ့ရမှာ ဖြစ်ပါတယ်။ အခြေအနေတွေ ရှုပ်ထွေးလာပြီးတဲ့နောက်မှာတော့ "
                    "သူတို့ရင်ဆိုင်ကြုံတွေ့ရမယ့် အန္တရာယ်တွေနဲ့ အဖြေရှာပုံတွေကို စိတ်ဝင်စားဖွယ် ဆက်လက်ရှုစားရမှာ ဖြစ်ပါတယ်။"
                )
        except Exception:
            burmese_script = (
                "ဇာတ်လမ်းအစမှာတော့ အဓိကဇာတ်ကောင်ရဲ့ ထူးခြားဆန်းကြယ်တဲ့ လှုပ်ရှားမှုတွေနဲ့အတူ "
                "မထင်မှတ်ထားတဲ့ အပြောင်းအလဲတွေကို မြင်တွေ့ရမှာ ဖြစ်ပါတယ်။ အခြေအနေတွေ ရှုပ်ထွေးလာပြီးတဲ့နောက်မှာတော့ "
                "သူတို့ရင်ဆိုင်ကြုံတွေ့ရမယ့် အန္တရာယ်တွေနဲ့ အဖြေရှာပုံတွေကို စိတ်ဝင်စားဖွယ် ဆက်လက်ရှုစားရမှာ ဖြစ်ပါတယ်။"
            )

        # ၃။ Edge TTS ဖြင့် မြန်မာအသံဖိုင် ဖန်တီးခြင်း
        communicate = edge_tts.Communicate(burmese_script, voice_name)
        await communicate.save(audio_path)

        # ၄။ မူရင်းဗီဒီယိုအရှည် အပြည့်အဝဖြင့် ပေါင်းစပ်ခြင်း
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
