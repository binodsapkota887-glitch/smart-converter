import os
import io
import time
import zipfile
import threading
import qrcode
import pytesseract
import cv2
import numpy as np
from flask import Flask, render_template_string, request, send_file, jsonify
from PIL import Image, ImageEnhance

app = Flask(__name__)

# configuration
PHOTO_URL = "https://smart-converter-ieh0.onrender.com/static/bs.jpg" 
UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

# Auto-Cleanup: १० मिनेट पुराना फाइलहरू हटाउने
def cleanup_files():
    while True:
        time.sleep(60)
        now = time.time()
        for f in os.listdir(UPLOAD_FOLDER):
            f_path = os.path.join(UPLOAD_FOLDER, f)
            if os.stat(f_path).st_mtime < now - 600:
                os.remove(f_path)

threading.Thread(target=cleanup_files, daemon=True).start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartConvert Ultimate | Binod Sapkota</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <style>
        :root { --neon: #22d3ee; --dark: #020617; }
        body { 
            background: var(--dark); color: white; font-family: 'Inter', sans-serif;
            background-image: url('{{ photo_url }}'); background-size: cover; background-attachment: fixed;
        }
        body::before { content: ""; position: fixed; inset: 0; background: radial-gradient(circle, rgba(15, 23, 42, 0.9), var(--dark)); z-index: -1; }
        
        .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }
        .neon-text { text-shadow: 0 0 15px var(--neon); }
        .neon-border { border: 1px solid var(--neon); box-shadow: 0 0 15px rgba(34, 211, 238, 0.2); }
        
        /* Scanner Effect */
        .scanner-line {
            position: absolute; width: 100%; height: 3px; background: var(--neon);
            top: 0; left: 0; z-index: 50; display: none;
            box-shadow: 0 0 20px var(--neon);
            animation: scanMove 2s linear infinite;
        }
        @keyframes scanMove { 0% { top: 0; } 100% { top: 100%; } }

        .nav-btn { font-size: 10px; font-weight: 900; letter-spacing: 2px; transition: 0.3s; opacity: 0.6; }
        .nav-btn.active { opacity: 1; color: var(--neon); border-bottom: 2px solid var(--neon); }
        
        input[type="file"]::file-selector-button { display: none; }
        .btn-main { background: linear-gradient(135deg, #22d3ee, #0ea5e9); color: black; font-weight: 900; transition: 0.4s; }
        .btn-main:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(34, 211, 238, 0.4); }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <nav class="p-8 flex justify-between items-center max-w-6xl mx-auto w-full animate__animated animate__fadeInDown">
        <div class="flex items-center gap-4">
            <div class="w-12 h-12 neon-border rounded-xl flex items-center justify-center font-black text-cyan-400 text-xl">S</div>
            <h1 class="text-2xl font-black italic tracking-tighter neon-text uppercase">Smart<span class="text-white">Convert</span></h1>
        </div>
        <div class="hidden md:flex gap-8">
            <button onclick="toggleModal()" class="bg-white/10 hover:bg-white/20 px-6 py-2 rounded-full text-[10px] font-bold tracking-widest border border-white/10 transition-all">TERMINAL CONTACT</button>
        </div>
    </nav>

    <main class="flex-grow flex items-center justify-center p-4">
        <div class="glass w-full max-w-3xl rounded-[3rem] p-10 md:p-16 relative overflow-hidden animate__animated animate__zoomIn">
            <div id="scanLine" class="scanner-line"></div>

            <div class="flex flex-wrap justify-center gap-6 md:gap-12 mb-12 border-b border-white/5 pb-6">
                <button onclick="switchTab('convert')" id="tab-convert" class="nav-btn active uppercase">Converter</button>
                <button onclick="switchTab('ai')" id="tab-ai" class="nav-btn uppercase">AI Fix</button>
                <button onclick="switchTab('ocr')" id="tab-ocr" class="nav-btn uppercase">OCR</button>
                <button onclick="switchTab('qr')" id="tab-qr" class="nav-btn uppercase">QR Gen</button>
                <button onclick="switchTab('privacy')" id="tab-privacy" class="nav-btn uppercase text-red-400">Privacy</button>
            </div>

            <div id="content-convert" class="tab-content">
                <form action="/process" method="POST" enctype="multipart/form-data" onsubmit="showLoading()">
                    <input type="hidden" name="mode" value="convert">
                    <div class="group border-2 border-dashed border-white/10 p-16 rounded-[2.5rem] text-center hover:border-cyan-500/50 transition-all relative cursor-pointer">
                        <input type="file" name="images" multiple required class="absolute inset-0 opacity-0 cursor-pointer" onchange="updateLabel(this, 'label-conv')">
                        <span class="text-5xl block mb-4">📂</span>
                        <p id="label-conv" class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Select Multiple Photos</p>
                    </div>
                    <div class="grid grid-cols-2 gap-4 mt-8">
                        <select name="format" class="bg-slate-900/80 border border-white/10 p-5 rounded-2xl text-[10px] font-black outline-none text-cyan-400">
                            <option value="PDF">COMBINED PDF</option>
                            <option value="ZIP">BATCH IMAGES (ZIP)</option>
                            <option value="PNG">PNG FORMAT</option>
                        </select>
                        <select name="quality" class="bg-slate-900/80 border border-white/10 p-5 rounded-2xl text-[10px] font-black outline-none">
                            <option value="95">95% QUALITY</option>
                            <option value="70">70% BALANCED</option>
                        </select>
                    </div>
                    <button type="submit" class="w-full mt-8 py-6 btn-main rounded-2xl text-[10px] uppercase tracking-[0.3em]">Initiate Conversion</button>
                </form>
            </div>

            <div id="content-ai" class="tab-content hidden">
                <form action="/process" method="POST" enctype="multipart/form-data" onsubmit="showLoading()">
                    <input type="hidden" name="mode" value="ai">
                    <div class="border-2 border-dashed border-white/10 p-16 rounded-[2.5rem] text-center relative">
                        <input type="file" name="images" required class="absolute inset-0 opacity-0 cursor-pointer" onchange="updateLabel(this, 'label-ai')">
                        <span class="text-5xl block mb-4">✨</span>
                        <p id="label-ai" class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest">AI Sharpness & Contrast</p>
                    </div>
                    <button type="submit" class="w-full mt-8 py-6 btn-main rounded-2xl text-[10px] uppercase tracking-[0.3em]">Enhance with AI</button>
                </form>
            </div>

            <div id="content-ocr" class="tab-content hidden">
                <div class="space-y-6">
                    <div class="border-2 border-dashed border-white/10 p-10 rounded-[2.5rem] text-center relative">
                        <input type="file" id="ocrInput" class="absolute inset-0 opacity-0 cursor-pointer" onchange="runOCR()">
                        <span class="text-4xl block mb-2">🔍</span>
                        <p class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Upload Image for OCR</p>
                    </div>
                    <textarea id="ocrResult" readonly class="w-full h-32 bg-black/40 border border-white/10 p-4 rounded-2xl text-xs text-cyan-400 outline-none" placeholder="Extracted text will appear here..."></textarea>
                </div>
            </div>

            <div id="content-qr" class="tab-content hidden">
                <div class="space-y-6 text-center">
                    <input type="text" id="qrText" placeholder="ENTER URL OR TEXT..." class="w-full bg-slate-900 border border-white/10 p-5 rounded-2xl text-[10px] font-bold outline-none text-center">
                    <button onclick="generateQR()" class="w-full py-6 btn-main rounded-2xl text-[10px] uppercase tracking-[0.3em]">Generate QR Code</button>
                    <div id="qrImg" class="flex justify-center mt-6"></div>
                </div>
            </div>

            <div id="content-privacy" class="tab-content hidden">
                <form action="/process" method="POST" enctype="multipart/form-data" onsubmit="showLoading()">
                    <input type="hidden" name="mode" value="privacy">
                    <div class="border-2 border-dashed border-red-500/20 p-16 rounded-[2.5rem] text-center relative bg-red-500/5">
                        <input type="file" name="images" required class="absolute inset-0 opacity-0 cursor-pointer" onchange="updateLabel(this, 'label-priv')">
                        <span class="text-5xl block mb-4">🎭</span>
                        <p id="label-priv" class="text-[10px] font-bold text-red-400 uppercase tracking-widest">Auto Face Detection & Blur</p>
                    </div>
                    <button type="submit" class="w-full mt-8 py-6 bg-red-600 text-black font-black rounded-2xl text-[10px] uppercase tracking-[0.3em]">Secure Identities</button>
                </form>
            </div>

        </div>
    </main>

    <footer class="p-8 text-center">
        <p class="text-[8px] font-bold tracking-[0.5em] opacity-30 uppercase">Secure Environment • All Data Wiped Every 10 Minutes</p>
    </footer>

    <div id="contactModal" class="fixed inset-0 bg-black/95 z-[100] hidden items-center justify-center p-6 backdrop-blur-2xl">
        <div class="glass p-12 max-w-sm w-full text-center rounded-[3rem] neon-border">
            <h3 class="text-3xl font-black italic mb-8 neon-text">BINOD SAPKOTA</h3>
            <div class="space-y-4">
                <a href="https://facebook.com/petter.boe" class="block p-5 bg-white/5 rounded-2xl text-[10px] font-bold tracking-widest hover:bg-cyan-500 hover:text-black transition-all">FACEBOOK</a>
                <a href="https://wa.me/9762418689" class="block p-5 bg-white/5 rounded-2xl text-[10px] font-bold tracking-widest hover:bg-cyan-500 hover:text-black transition-all">WHATSAPP</a>
                <button onclick="toggleModal()" class="mt-4 text-[10px] opacity-40 uppercase">Close Terminal</button>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('content-' + tab).classList.remove('hidden');
            document.getElementById('tab-' + tab).classList.add('active');
        }
        function toggleModal() { document.getElementById('contactModal').classList.toggle('flex'); document.getElementById('contactModal').classList.toggle('hidden'); }
        function showLoading() { document.getElementById('scanLine').style.display = 'block'; }
        function updateLabel(input, id) { document.getElementById(id).innerText = input.files.length + " FILE(S) READY"; }

        async function generateQR() {
            const val = document.getElementById('qrText').value;
            if(!val) return alert("Enter content!");
            const res = await fetch('/api/qr', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text: val}) });
            const blob = await res.blob();
            document.getElementById('qrImg').innerHTML = `<img src="${URL.createObjectURL(blob)}" class="w-48 h-48 neon-border p-2 bg-white rounded-xl animate__animated animate__fadeIn">`;
        }

        async function runOCR() {
            const file = document.getElementById('ocrInput').files[0];
            const formData = new FormData();
            formData.append('image', file);
            document.getElementById('ocrResult').value = "SCANNING TEXT...";
            const res = await fetch('/api/ocr', { method: 'POST', body: formData });
            const data = await res.json();
            document.getElementById('ocrResult').value = data.text || "No text detected.";
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, photo_url=PHOTO_URL)

@app.route('/process', methods=['POST'])
def process():
    mode = request.form.get('mode')
    files = request.files.getlist('images')
    if not files or files[0].filename == '': return "Error: No files selected", 400

    out_io = io.BytesIO()

    # 1. Standard Converter & Batch
    if mode == 'convert':
        fmt = request.form.get('format')
        q = int(request.form.get('quality', 95))
        
        if fmt == 'ZIP':
            with zipfile.ZipFile(out_io, 'w') as zf:
                for i, f in enumerate(files):
                    img = Image.open(f).convert('RGB')
                    b = io.BytesIO()
                    img.save(b, format='JPEG', quality=q)
                    zf.writestr(f"smart_{i+1}.jpg", b.getvalue())
            out_io.seek(0)
            return send_file(out_io, mimetype="application/zip", as_attachment=True, download_name="SmartBatch.zip")
        
        elif fmt == 'PDF':
            imgs = [Image.open(f).convert('RGB') for f in files]
            imgs[0].save(out_io, format='PDF', save_all=True, append_images=imgs[1:])
            out_io.seek(0)
            return send_file(out_io, mimetype="application/pdf", as_attachment=True, download_name="SmartConvert.pdf")

    # 2. AI Enhancer
    elif mode == 'ai':
        img = Image.open(files[0]).convert('RGB')
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Sharpness(img).enhance(1.6)
        img.save(out_io, format='JPEG', quality=100)
        out_io.seek(0)
        return send_file(out_io, mimetype="image/jpeg", as_attachment=True, download_name="AI_Enhanced.jpg")

    # 3. Privacy (Face Blur)
    elif mode == 'privacy':
        img_np = np.frombuffer(files[0].read(), np.uint8)
        img_cv = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY), 1.1, 4)
        for (x, y, w, h) in faces:
            img_cv[y:y+h, x:x+w] = cv2.GaussianBlur(img_cv[y:y+h, x:x+w], (99, 99), 30)
        _, buffer = cv2.imencode('.jpg', img_cv)
        return send_file(io.BytesIO(buffer), mimetype="image/jpeg", as_attachment=True, download_name="SecureBlur.jpg")

@app.route('/api/qr', methods=['POST'])
def api_qr():
    data = request.json.get('text')
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/api/ocr', methods=['POST'])
def api_ocr():
    f = request.files['image']
    text = pytesseract.image_to_string(Image.open(f))
    return jsonify({'text': text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
