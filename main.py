import os
import io
import time
import threading
import qrcode
import pytesseract
from flask import Flask, render_template_string, request, send_file, jsonify
from PIL import Image

app = Flask(__name__)

# एसेट्स र कन्फिगरेसन
PHOTO_URL = "https://smart-converter-ieh0.onrender.com/static/bs.jpg" 
VIDEO_URL = "https://smart-converter-ieh0.onrender.com/static/an.mp4"
UPLOAD_FOLDER = 'temp_uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# फिचर: १० मिनेटपछि डाटा हटाउने फङ्ग्सन
def cleanup_old_files():
    while True:
        time.sleep(60)
        now = time.time()
        for f in os.listdir(UPLOAD_FOLDER):
            f_path = os.path.join(UPLOAD_FOLDER, f)
            if os.stat(f_path).st_mtime < now - 600:
                if os.path.isfile(f_path):
                    os.remove(f_path)

threading.Thread(target=cleanup_old_files, daemon=True).start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartConvert Pro | Binod Sapkota</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <style>
        body { 
            background: #020617; color: white; font-family: 'Inter', sans-serif;
            background-image: url('{{ photo_url }}'); background-size: cover; background-attachment: fixed;
        }
        body::before { content: ""; position: fixed; inset: 0; background: radial-gradient(circle at center, rgba(15, 23, 42, 0.8), #020617); z-index: -1; }
        
        .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .neon-border { border: 1px solid #22d3ee; box-shadow: 0 0 15px rgba(34, 211, 238, 0.3); }
        .tab-btn { transition: 0.3s; border-bottom: 2px solid transparent; }
        .tab-btn.active { border-color: #22d3ee; color: #22d3ee; }
        
        .preview-img { width: 80px; height: 80px; object-fit: cover; border-radius: 10px; border: 1px solid #22d3ee; }
        
        @keyframes pulse-cyan { 0% { box-shadow: 0 0 0 0 rgba(34, 211, 238, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(34, 211, 238, 0); } 100% { box-shadow: 0 0 0 0 rgba(34, 211, 238, 0); } }
        .btn-glow { animation: pulse-cyan 2s infinite; }
    </style>
</head>
<body class="min-h-screen">

    <nav class="p-6 flex justify-between items-center max-w-6xl mx-auto">
        <h1 class="text-2xl font-black italic tracking-tighter animate__animated animate__fadeInLeft">
            SMART<span class="text-cyan-400">CONVERTER</span> <span class="text-[10px] bg-cyan-500/20 px-2 py-1 rounded ml-2">PRO</span>
        </h1>
        <div class="flex gap-4 items-center animate__animated animate__fadeInRight">
            <span class="hidden md:block text-[10px] font-bold text-cyan-400 border border-cyan-400/30 px-3 py-1 rounded-full">SECURE ENCRYPTION ACTIVE</span>
            <button onclick="toggleModal()" class="bg-white text-black px-6 py-2 rounded-full text-[11px] font-bold hover:bg-cyan-400 transition-all">CONTACT</button>
        </div>
    </nav>

    <main class="max-w-4xl mx-auto p-4 mt-10">
        <div class="glass rounded-[3rem] p-8 md:p-12 shadow-2xl animate__animated animate__zoomIn">
            
            <div class="flex justify-center gap-8 mb-10 border-b border-white/10">
                <button onclick="showTab('convert-tab')" class="tab-btn active pb-4 font-bold uppercase text-xs tracking-widest" id="btn-conv">Convert</button>
                <button onclick="showTab('qr-tab')" class="tab-btn pb-4 font-bold uppercase text-xs tracking-widest" id="btn-qr">QR Gen</button>
                <button onclick="showTab('ocr-tab')" class="tab-btn pb-4 font-bold uppercase text-xs tracking-widest" id="btn-ocr">OCR</button>
            </div>

            <div id="convert-tab" class="tab-content">
                <form action="/convert" method="POST" enctype="multipart/form-data">
                    <div class="border-2 border-dashed border-cyan-500/30 p-10 rounded-3xl text-center relative hover:bg-white/5 transition-all">
                        <input type="file" name="images" multiple class="absolute inset-0 opacity-0 cursor-pointer" onchange="previewImages(this)">
                        <p class="text-3xl mb-2">📸</p>
                        <p class="text-[10px] font-bold uppercase opacity-60">Drop Images or Click to Upload</p>
                        <div id="p-grid" class="flex flex-wrap gap-2 mt-4 justify-center"></div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                        <select name="format" class="bg-slate-900 border border-white/10 p-4 rounded-2xl text-xs font-bold outline-none">
                            <option value="PDF">COMBINE TO PDF</option>
                            <option value="PNG">TO PNG</option>
                            <option value="JPEG">TO JPEG (COMPRESSED)</option>
                        </select>
                        <input type="number" name="quality" placeholder="Quality (1-100)" class="bg-slate-900 border border-white/10 p-4 rounded-2xl text-xs font-bold outline-none" value="95">
                    </div>

                    <button type="submit" class="w-full mt-6 py-5 bg-cyan-500 text-black font-black text-xs rounded-2xl btn-glow uppercase">Start Conversion ↗</button>
                </form>
            </div>

            <div id="qr-tab" class="tab-content hidden">
                <div class="space-y-4">
                    <input type="text" id="qr-input" placeholder="Enter URL or Text for QR..." class="w-full bg-slate-900 border border-white/10 p-5 rounded-2xl text-xs outline-none">
                    <button onclick="generateQR()" class="w-full py-5 bg-white text-black font-black text-xs rounded-2xl uppercase">Generate QR Code</button>
                    <div id="qr-result" class="flex justify-center mt-6"></div>
                </div>
            </div>

            <div id="ocr-tab" class="tab-content hidden text-center">
                <div class="border-2 border-dashed border-white/10 p-10 rounded-3xl mb-6">
                    <input type="file" id="ocr-file" class="hidden" onchange="runOCR(this)">
                    <label for="ocr-file" class="cursor-pointer">
                        <p class="text-3xl mb-2">🔍</p>
                        <p class="text-[10px] font-bold uppercase">Upload image to extract text</p>
                    </label>
                </div>
                <textarea id="ocr-text" class="w-full h-40 bg-black/40 border border-white/10 p-4 rounded-2xl text-xs text-cyan-400 outline-none" readonly placeholder="Result will appear here..."></textarea>
            </div>

        </div>
        <p class="text-[9px] text-center mt-8 opacity-40 uppercase tracking-[0.3em]">Built for security • Auto-purges every 10 mins</p>
    </main>

    <div id="contactModal" class="fixed inset-0 bg-black/95 z-50 hidden items-center justify-center p-6 backdrop-blur-xl">
        <div class="glass p-10 max-w-sm w-full text-center rounded-[3rem] neon-border relative">
            <button onclick="toggleModal()" class="absolute top-6 right-6 opacity-50">✕</button>
            <h3 class="text-2xl font-black italic mb-8 uppercase">Binod Sapkota</h3>
            <div class="space-y-3">
                <a href="https://facebook.com/petter.boe" class="block p-4 bg-white/5 rounded-2xl text-[10px] font-bold uppercase hover:bg-cyan-500 hover:text-black transition-all">Facebook</a>
                <a href="https://wa.me/9762418689" class="block p-4 bg-white/5 rounded-2xl text-[10px] font-bold uppercase hover:bg-cyan-500 hover:text-black transition-all">WhatsApp</a>
            </div>
        </div>
    </div>

    <script>
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.remove('hidden');
            event.currentTarget.classList.add('active');
        }

        function toggleModal() { document.getElementById('contactModal').classList.toggle('flex'); document.getElementById('contactModal').classList.toggle('hidden'); }

        function previewImages(input) {
            const grid = document.getElementById('p-grid');
            grid.innerHTML = '';
            Array.from(input.files).forEach(file => {
                const reader = new FileReader();
                reader.onload = e => {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'preview-img animate__animated animate__fadeIn';
                    grid.appendChild(img);
                };
                reader.readAsDataURL(file);
            });
        }

        async function generateQR() {
            const text = document.getElementById('qr-input').value;
            if(!text) return alert("Please enter some text");
            const response = await fetch('/generate_qr', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            });
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            document.getElementById('qr-result').innerHTML = `<img src="${url}" class="w-48 h-48 neon-border rounded-xl p-2 bg-white">`;
        }

        async function runOCR(input) {
            const formData = new FormData();
            formData.append('image', input.files[0]);
            document.getElementById('ocr-text').value = "Scanning... Please wait...";
            const response = await fetch('/ocr', { method: 'POST', body: formData });
            const data = await response.json();
            document.getElementById('ocr-text').value = data.text || "No text found.";
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, photo_url=PHOTO_URL, video_url=VIDEO_URL)

@app.route('/convert', methods=['POST'])
def convert():
    files = request.files.getlist('images')
    target_format = request.form.get('format', 'PDF').upper()
    quality = int(request.form.get('quality', 95))
    
    if not files or files[0].filename == '': return "No files", 400
    
    imgs = [Image.open(f).convert('RGB') for f in files]
    out = io.BytesIO()
    
    if target_format == 'PDF':
        imgs[0].save(out, format='PDF', save_all=True, append_images=imgs[1:])
        mimetype, name = "application/pdf", "SmartConvert_Pro.pdf"
    else:
        imgs[0].save(out, target_format, quality=quality)
        mimetype, name = f"image/{target_format.lower()}", f"converted.{target_format.lower()}"
    
    out.seek(0)
    return send_file(out, mimetype=mimetype, as_attachment=True, download_name=name)

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.json.get('text')
    qr = qrcode.make(data)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/ocr', methods=['POST'])
def ocr_process():
    file = request.files['image']
    img = Image.open(file)
    text = pytesseract.image_to_string(img)
    return jsonify({'text': text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    import os
import io
import time
import zipfile
import threading
import cv2
import numpy as np
from flask import Flask, render_template_string, request, send_file, jsonify
from PIL import Image, ImageEnhance

app = Flask(__name__)

# Config & Paths
PHOTO_URL = "https://smart-converter-ieh0.onrender.com/static/bs.jpg" 
VIDEO_URL = "https://smart-converter-ieh0.onrender.com/static/an.mp4"
UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

def cleanup_files():
    while True:
        time.sleep(60)
        now = time.time()
        for f in os.listdir(UPLOAD_FOLDER):
            if os.stat(os.path.join(UPLOAD_FOLDER, f)).st_mtime < now - 600:
                os.remove(os.path.join(UPLOAD_FOLDER, f))

threading.Thread(target=cleanup_files, daemon=True).start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartConvert Pro v2 | Binod Sapkota</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <style>
        :root { --neon: #22d3ee; }
        body { background: #020617; color: white; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .glass { background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); }
        .neon-text { text-shadow: 0 0 10px var(--neon); }
        
        /* Scanning Animation */
        .scanner-line {
            position: absolute; width: 100%; height: 2px; background: var(--neon);
            top: 0; left: 0; z-index: 10; display: none;
            box-shadow: 0 0 15px var(--neon);
            animation: scan 2s linear infinite;
        }
        @keyframes scan { 0% { top: 0; } 100% { top: 100%; } }
        
        .tab-btn { transition: 0.4s; opacity: 0.5; }
        .tab-btn.active { opacity: 1; border-bottom: 2px solid var(--neon); color: var(--neon); }
        .btn-premium { background: linear-gradient(90deg, #22d3ee, #0ea5e9); color: black; font-weight: 900; transition: 0.3s; }
        .btn-premium:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(34, 211, 238, 0.4); }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <nav class="p-8 flex justify-between items-center max-w-7xl mx-auto w-full">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-cyan-500 rounded-lg flex items-center justify-center font-black text-black">S</div>
            <h1 class="text-2xl font-black tracking-tighter uppercase italic neon-text">Smart<span class="text-white">Converter</span></h1>
        </div>
        <div class="hidden md:flex gap-6 text-[10px] font-bold tracking-[0.2em] opacity-60">
            <span>AI ENHANCER ON</span>
            <span>SECURE BATCH ZIP</span>
            <span>FACE PRIVACY ACTIVE</span>
        </div>
    </nav>

    <main class="flex-grow container mx-auto px-4 py-10 max-w-4xl">
        <div class="glass rounded-[3.5rem] p-8 md:p-14 relative overflow-hidden animate__animated animate__fadeInUp">
            <div id="scanLine" class="scanner-line"></div>
            
            <div class="flex justify-center gap-10 mb-12">
                <button onclick="switchTab('batch')" id="tab-batch" class="tab-btn active text-xs font-black uppercase tracking-widest">Batch Process</button>
                <button onclick="switchTab('ai')" id="tab-ai" class="tab-btn text-xs font-black uppercase tracking-widest">AI Enhancer</button>
                <button onclick="switchTab('privacy')" id="tab-privacy" class="tab-btn text-xs font-black uppercase tracking-widest">Privacy (Blur)</button>
            </div>

            <div id="section-batch" class="tab-content">
                <form action="/process" method="POST" enctype="multipart/form-data" onsubmit="startScan()">
                    <input type="hidden" name="mode" value="batch">
                    <div class="group border-2 border-dashed border-white/10 p-16 rounded-[2.5rem] text-center hover:border-cyan-500/50 transition-all cursor-pointer relative">
                        <input type="file" name="images" multiple required class="absolute inset-0 opacity-0 cursor-pointer" onchange="updateFiles(this)">
                        <div id="upload-icon" class="text-5xl mb-4 group-hover:scale-110 transition-transform">📁</div>
                        <p id="file-count" class="text-xs font-bold text-slate-400 uppercase">Upload Multiple Images</p>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4 mt-8">
                        <select name="format" class="bg-black/50 border border-white/10 p-5 rounded-2xl text-[11px] font-bold outline-none text-cyan-400">
                            <option value="ZIP">DOWNLOAD ALL (ZIP)</option>
                            <option value="PDF">COMBINE TO PDF</option>
                            <option value="JPEG">JPEG (INDIVIDUAL)</option>
                        </select>
                        <select name="quality" class="bg-black/50 border border-white/10 p-5 rounded-2xl text-[11px] font-bold outline-none">
                            <option value="95">ULTRA HD (95%)</option>
                            <option value="70">BALANCED (70%)</option>
                            <option value="40">LOW SIZE (40%)</option>
                        </select>
                    </div>
                    <button type="submit" class="w-full mt-8 py-6 btn-premium rounded-2xl text-[11px] uppercase tracking-widest">Execute Batch Command</button>
                </form>
            </div>

            <div id="section-ai" class="tab-content hidden">
                <form action="/process" method="POST" enctype="multipart/form-data" onsubmit="startScan()">
                    <input type="hidden" name="mode" value="enhance">
                    <div class="border-2 border-dashed border-white/10 p-16 rounded-[2.5rem] text-center">
                        <input type="file" name="images" required class="absolute opacity-0 cursor-pointer w-full h-full left-0 top-0">
                        <p class="text-xs font-bold text-cyan-400 uppercase">AI Auto-Fix & Sharpen</p>
                    </div>
                    <button type="submit" class="w-full mt-8 py-6 btn-premium rounded-2xl text-[11px] uppercase">Enhance Image ⚡</button>
                </form>
            </div>

            <div id="section-privacy" class="tab-content hidden">
                <form action="/process" method="POST" enctype="multipart/form-data" onsubmit="startScan()">
                    <input type="hidden" name="mode" value="blur">
                    <div class="border-2 border-dashed border-white/10 p-16 rounded-[2.5rem] text-center">
                        <input type="file" name="images" required class="absolute opacity-0 cursor-pointer w-full h-full left-0 top-0">
                        <p class="text-xs font-bold text-red-400 uppercase">Auto Face Detection & Blur</p>
                    </div>
                    <button type="submit" class="w-full mt-8 py-6 bg-red-500 text-white font-black rounded-2xl text-[11px] uppercase">Secure & Blur Faces</button>
                </form>
            </div>
        </div>
    </main>

    <script>
        function switchTab(id) {
            document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('section-' + id).classList.remove('hidden');
            document.getElementById('tab-' + id).classList.add('active');
        }
        function startScan() { document.getElementById('scanLine').style.display = 'block'; }
        function updateFiles(input) {
            document.getElementById('file-count').innerText = input.files.length + " Files Selected";
            document.getElementById('upload-icon').innerText = "✅";
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process():
    mode = request.form.get('mode')
    files = request.files.getlist('images')
    if not files or files[0].filename == '': return "No files", 400

    out_io = io.BytesIO()
    
    # 1. Batch Processing (ZIP/PDF)
    if mode == 'batch':
        target = request.form.get('format')
        quality = int(request.form.get('quality', 95))
        
        if target == 'ZIP':
            with zipfile.ZipFile(out_io, 'w') as zf:
                for i, f in enumerate(files):
                    img = Image.open(f).convert('RGB')
                    img_byte = io.BytesIO()
                    img.save(img_byte, format='JPEG', quality=quality)
                    zf.writestr(f"image_{i+1}.jpg", img_byte.getvalue())
            out_io.seek(0)
            return send_file(out_io, mimetype="application/zip", as_attachment=True, download_name="Batch_Converted.zip")
        
        elif target == 'PDF':
            imgs = [Image.open(f).convert('RGB') for f in files]
            imgs[0].save(out_io, format='PDF', save_all=True, append_images=imgs[1:])
            out_io.seek(0)
            return send_file(out_io, mimetype="application/pdf", as_attachment=True, download_name="Combined_Pro.pdf")

    # 2. AI Enhancement
    elif mode == 'enhance':
        img = Image.open(files[0]).convert('RGB')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2) # Contrast Up
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5) # Sharpness Up
        img.save(out_io, format='JPEG', quality=100)
        out_io.seek(0)
        return send_file(out_io, mimetype="image/jpeg", as_attachment=True, download_name="AI_Enhanced.jpg")

    # 3. Face Blur (OpenCV)
    elif mode == 'blur':
        # PIL to OpenCV
        img_data = np.frombuffer(files[0].read(), np.uint8)
        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        for (x, y, w, h) in faces:
            sub_face = img[y:y+h, x:x+w]
            sub_face = cv2.GaussianBlur(sub_face, (99, 99), 30)
            img[y:y+h, x:x+w] = sub_face
            
        _, buffer = cv2.imencode('.jpg', img)
        return send_file(io.BytesIO(buffer), mimetype="image/jpeg", as_attachment=True, download_name="Privacy_Blurred.jpg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
