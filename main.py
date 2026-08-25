from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import asyncio
import os
import shutil
import traceback
from moviepy import VideoFileClip, AudioFileClip

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
    <title>Auto Video Recap & Editor</title>
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
        .btn { width: 100%; padding: 16px; background: #2563eb; color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; }
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
                <h1>Auto Video Recap & Editor</h1>
                <p class="sub">Copyright-safe Burmese recapping tool</p>
            </div>
        </div>

        <div class="upload-card" onclick="document.getElementById('videoFile').click()">
            <div style="font-size: 32px; margin-bottom: 8px;">📤</div>
            <strong id="file-label" style="font-size: 14px; color: #cbd5e1;">SELECT INPUT VIDEO (MP4)</strong>
            <p style="font-size: 11px; color: #64748b; margin-top: 4px;">Click to browse from phone</p>
        </div>
        <input type="file" id="videoFile" accept="video/*" onchange="fileSelected(this)">

        <label style="font-size: 12px; color: #94a3b8; margin-bottom: 6px; display: block;">Burmese Voice:</label>
        <select id="voice" class="voice-select">
            <option value="my-MM-ThihaNeural">Thiha (Male Voice)</option>
            <option value="my-MM-NilarNeural">Nilar (Female Voice)</option>
        </select>

        <button id="submitBtn" class="btn" onclick="processVideo()">🚀 START AUTO RECAP</button>

        <div id="status"></div>

        <div id="result-area">
            <h3 style="font-size: 14px; color: #4ade80;">✅ Recap Video Ready!</h3>
            <video id="previewPlayer" controls playsinline></video>
            <a id="downBtn" class="btn-down" download="burmese_recap.mp4">📥 DOWNLOAD RECAP VIDEO</a>
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
            btn.innerText = "⏳ Processing Video...";
            status.innerText = "Generating Burmese narration & processing video... Please wait (about 15-30s).";
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
                    const errText = await response.text();
                    throw new Error(errText || "Status code: " + response.status);
                }

                const blob = await response.blob();
                const videoUrl = URL.createObjectURL(blob);
                
                const previewPlayer = document.getElementById('previewPlayer');
                previewPlayer.src = videoUrl;
                
                const downBtn = document.getElementById('downBtn');
                downBtn.href = videoUrl;
                
                resultArea.style.display = "block";
                status.innerText = "Done! Download or play below.";
            } catch (err) {
                alert("Error: " + err.message);
                status.innerText = "Error details: " + err.message;
            } finally {
                btn.disabled = false;
                btn.innerText = "🚀 START AUTO RECAP";
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
        # Save video
        with open(input_video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # Generate Burmese TTS
        burmese_script = "မင်္ဂလာပါခင်ဗျာ။ ဒါကတော့ AI ကနေ အလိုအလျောက် မြန်မာဘာသာနဲ့ ပြန်လည်ရှင်းပြပေးထားတဲ့ Video Recap ဖြစ်ပါတယ်။"
        communicate = edge_tts.Communicate(burmese_script, voice_name)
        await communicate.save(audio_path)

        # Merge Audio & Video
        video_clip = VideoFileClip(input_video_path)
        audio_clip = AudioFileClip(audio_path)

        # Match audio duration or keep video intact
        if hasattr(video_clip, 'with_audio'):
            final_clip = video_clip.with_audio(audio_clip)
        else:
            final_clip = video_clip.set_audio(audio_clip)

        final_clip.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2,
            logger=None
        )

        video_clip.close()
        audio_clip.close()

        return FileResponse(
            path=output_video_path,
            filename=f"burmese_{safe_name}",
            media_type="video/mp4"
        )
    except Exception as e:
        error_msg = traceback.format_exc()
        print("Error during video processing:", error_msg)
        raise HTTPException(status_code=500, detail=str(e))
